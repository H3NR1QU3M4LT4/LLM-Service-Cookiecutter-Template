"""Semantic Kernel chat client: Azure OpenAI (Foundry) first, Ollama as fallback, JSON out, retry per provider."""

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx
from azure.identity import DefaultAzureCredential
from ollama import ResponseError as OllamaResponseError
from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion, OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import KernelException
from semantic_kernel.functions import FunctionResult, KernelArguments
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from config import Settings
from llm.prompts import Prompt, load_prompt

logger = logging.getLogger(__name__)

# KernelException/httpx.HTTPError/OllamaResponseError/ConnectionError: provider and transport failures (the Ollama
# client raises its own errors, unwrapped by Semantic Kernel). ValueError: empty content, bad JSON or schema mismatch
# (json.JSONDecodeError and pydantic.ValidationError both subclass it) - a retry usually fixes these.
_RETRYABLE = (KernelException, httpx.HTTPError, OllamaResponseError, ConnectionError, TimeoutError, ValueError)

_MAX_LOGGED_CHARS = 2000
_ASK_PROMPT = load_prompt("ask")
PROMPT_VERSIONS = {_ASK_PROMPT.name: _ASK_PROMPT.version}


def _token_usage(reply: FunctionResult | None) -> tuple[int | None, int | None]:
    """Return (input, output) token counts from the provider's usage metadata, None when it reports none."""
    contents = reply.value if reply is not None and reply.value else []
    usage = contents[0].metadata.get("usage") if contents else None
    return getattr(usage, "prompt_tokens", None), getattr(usage, "completion_tokens", None)


class LLMUnavailableError(Exception):
    """Every configured provider failed."""


@dataclass(frozen=True)
class Completion[T: BaseModel]:
    """A validated answer with how it was produced (used by the evals; the API only needs the answer)."""

    result: T
    provider: str
    model: str
    prompt: str
    prompt_version: str
    attempts: int
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True)
class Provider:
    """A chat service registered on the kernel under `name`, and how to ask it for JSON conforming to a model."""

    name: str
    model: str
    settings_for: Callable[[type[BaseModel], float | None], PromptExecutionSettings]


def _azure_settings(schema: type[BaseModel], temperature: float | None) -> PromptExecutionSettings:
    return AzureChatPromptExecutionSettings(response_format=schema, temperature=temperature)


def _ollama_settings(schema: type[BaseModel], temperature: float | None) -> PromptExecutionSettings:
    options = None if temperature is None else {"temperature": temperature}
    return OllamaChatPromptExecutionSettings(format=schema.model_json_schema(), options=options)


def build_kernel(settings: Settings) -> tuple[Kernel, list[Provider]]:
    """Build the kernel with its chat services and the providers in priority order.

    Azure is skipped when its endpoint is not configured.
    """
    kernel = Kernel()
    providers: list[Provider] = []
    if settings.azure_openai_endpoint:
        # API key only locally; every other environment authenticates with Entra ID (managed identity in Azure).
        api_key = settings.azure_openai_api_key if settings.environment == "local" else ""
        azure = AzureChatCompletion(
            service_id="azure",
            deployment_name=settings.azure_openai_deployment,
            endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            api_key=api_key,
            credential=None if api_key else DefaultAzureCredential(),
        )
        kernel.add_service(azure)
        providers.append(Provider("azure", settings.azure_openai_deployment, _azure_settings))
    kernel.add_service(
        OllamaChatCompletion(service_id="ollama", ai_model_id=settings.ollama_model, host=settings.ollama_host)
    )
    providers.append(Provider("ollama", settings.ollama_model, _ollama_settings))
    return kernel, providers


class LLMClient:
    """Asks providers in order, retrying each with exponential backoff before moving to the next."""

    def __init__(self, kernel: Kernel, providers: list[Provider], settings: Settings) -> None:
        """Create the client.

        Args:
            kernel: Kernel holding one chat service per provider, registered under the provider's name.
            providers: Providers in priority order; the first is primary.
            settings: Source of the retry configuration.
        """
        self.kernel = kernel
        self.providers = providers
        self._settings = settings

    async def complete_json[T: BaseModel](
        self,
        prompt: str,
        schema: type[T],
        *,
        template: Prompt = _ASK_PROMPT,
        temperature: float | None = None,
        variables: dict[str, str] | None = None,
    ) -> tuple[T, str]:
        """Get a JSON answer validated against `schema`.

        Args:
            prompt: The user prompt.
            schema: Pydantic model the answer must conform to.
            template: Prompt template to use; defaults to the versioned `ask` prompt.
            temperature: Sampling temperature; None keeps the provider's default.
            variables: Extra template variables (HTML-encoded by the engine, like `question`).

        Returns:
            The validated answer and the name of the provider that produced it.

        Raises:
            LLMUnavailableError: If every provider exhausted its attempts.
        """
        completion = await self.complete(
            prompt, schema, template=template, temperature=temperature, variables=variables
        )
        return completion.result, completion.provider

    async def complete[T: BaseModel](
        self,
        prompt: str,
        schema: type[T],
        *,
        template: Prompt = _ASK_PROMPT,
        temperature: float | None = None,
        variables: dict[str, str] | None = None,
    ) -> Completion[T]:
        """Like `complete_json`, but also return the model, prompt version, attempts, latency and token counts.

        Raises:
            LLMUnavailableError: If every provider exhausted its attempts.
        """
        for provider in self.providers:
            try:
                return await self._ask(provider, prompt, schema, template, temperature, variables or {})
            except _RETRYABLE as exc:
                logger.warning(
                    "llm.provider_failed", extra={"provider": provider.name, "error_type": type(exc).__name__}
                )
        raise LLMUnavailableError("All LLM providers failed.")

    async def _ask[T: BaseModel](
        self,
        provider: Provider,
        prompt: str,
        schema: type[T],
        template: Prompt,
        temperature: float | None,
        variables: dict[str, str],
    ) -> Completion[T]:
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self._settings.llm_max_attempts),
            wait=wait_exponential_jitter(
                multiplier=self._settings.llm_retry_min_wait_seconds, max=self._settings.llm_retry_max_wait_seconds
            ),
            retry=retry_if_exception_type(_RETRYABLE),
            before_sleep=lambda state: logger.warning(
                "llm.retry", extra={"provider": provider.name, "attempt": state.attempt_number}
            ),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                return await self._attempt(
                    provider, prompt, schema, template, temperature, variables, attempt.retry_state.attempt_number
                )
        raise AssertionError("unreachable")  # pragma: no cover

    async def _attempt[T: BaseModel](
        self,
        provider: Provider,
        prompt: str,
        schema: type[T],
        template: Prompt,
        temperature: float | None,
        variables: dict[str, str],
        number: int,
    ) -> Completion[T]:
        """Make one call and log it: `llm.completed` on success, `llm.attempt_failed` (then re-raise) otherwise."""
        fields: dict[str, object] = {
            "provider": provider.name,
            "model": provider.model,
            "prompt": template.name,
            "prompt_version": template.version,
            "attempt": number,
        }
        if self._settings.should_log_llm_content:
            fields["input"] = prompt[:_MAX_LOGGED_CHARS]
        started = time.perf_counter()
        content = ""
        try:
            reply = await asyncio.wait_for(
                self.kernel.invoke_prompt(
                    prompt=template.config.template or "",
                    prompt_template_config=template.config,
                    arguments=KernelArguments(
                        settings={provider.name: provider.settings_for(schema, temperature)},
                        schema=json.dumps(schema.model_json_schema()),
                        question=prompt,
                        **variables,
                    ),
                ),
                timeout=self._settings.llm_timeout_seconds,
            )
            content = str(reply) if reply is not None else ""
            if not content:
                raise ValueError("Empty LLM response.")
            result = schema.model_validate_json(content)
        except _RETRYABLE as exc:
            fields.update(
                latency_ms=round((time.perf_counter() - started) * 1000),
                error_type=type(exc).__name__,
                error=str(exc)[:_MAX_LOGGED_CHARS],
            )
            if self._settings.should_log_llm_content and content:
                fields["output"] = content[:_MAX_LOGGED_CHARS]
            logger.warning("llm.attempt_failed", extra=fields)
            raise
        input_tokens, output_tokens = _token_usage(reply)
        latency_ms = round((time.perf_counter() - started) * 1000)
        fields.update(latency_ms=latency_ms, input_tokens=input_tokens, output_tokens=output_tokens)
        if self._settings.should_log_llm_content:
            fields["output"] = content[:_MAX_LOGGED_CHARS]
        logger.info("llm.completed", extra=fields)
        return Completion(
            result=result,
            provider=provider.name,
            model=provider.model,
            prompt=template.name,
            prompt_version=template.version,
            attempts=number,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
