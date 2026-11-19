import asyncio
import logging
from collections.abc import Callable, Iterator
from types import SimpleNamespace
from typing import Literal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from azure.core.exceptions import ClientAuthenticationError
from openai import OpenAIError
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.functions import KernelArguments

import telemetry
from config import Settings, get_settings
from llm import client
from llm.client import LLMClient, LLMUnavailableError, Provider
from main import app
from models.llm import Answer
from routes.deps import get_llm_client

SERVICES: dict[str, MagicMock] = {}
GOOD = '{"answer": "42", "confidence": 0.9}'


def _provider(name: str, replies: list[object]) -> Provider:
    service = AsyncMock(side_effect=replies)
    provider = Provider(name, f"{name}-model", lambda schema, temperature: MagicMock())
    SERVICES[name] = service
    return provider


def _kernel() -> MagicMock:
    kernel = MagicMock()

    async def invoke_prompt(arguments: KernelArguments, **_: object) -> object:
        assert arguments.execution_settings is not None
        return await SERVICES[next(iter(arguments.execution_settings))]()

    kernel.invoke_prompt = invoke_prompt
    return kernel


class _Reply:
    def __init__(self, content: str | None) -> None:
        self.content = content or ""
        usage = SimpleNamespace(prompt_tokens=5, completion_tokens=7)
        self.value = [SimpleNamespace(metadata={"usage": usage})]

    def __str__(self) -> str:
        return self.content


def _reply(content: str | None) -> _Reply:
    return _Reply(content)


@pytest.fixture
def client_with() -> Iterator[Callable[[list[Provider]], TestClient]]:
    def make(providers: list[Provider]) -> TestClient:
        settings = Settings(llm_max_attempts=2, llm_retry_min_wait_seconds=0, llm_retry_max_wait_seconds=0)
        app.dependency_overrides[get_llm_client] = lambda: LLMClient(_kernel(), providers, settings)
        return TestClient(app)

    yield make
    app.dependency_overrides.clear()


def test_status_lists_providers(client_with: Callable[[list[Provider]], TestClient]) -> None:
    client = client_with([_provider("azure", []), _provider("ollama", [])])
    body = client.get("/status").json()
    assert body["status"] == "ok"
    assert body["version"] == "0.0.1"
    assert body["environment"] == "local"
    assert body["prompts"] == {"ask": "1.1.0"}
    assert [(p["name"], p["role"]) for p in body["providers"]] == [("azure", "primary"), ("ollama", "fallback")]


def test_ask_uses_primary(client_with: Callable[[list[Provider]], TestClient]) -> None:
    client = client_with([_provider("azure", [_reply(GOOD)]), _provider("ollama", [])])
    response = client.post("/ask", json={"question": "q"})
    assert response.status_code == 200
    assert response.json() == {"result": Answer(answer="42", confidence=0.9).model_dump(), "provider": "azure"}


def test_ask_retries_then_succeeds(client_with: Callable[[list[Provider]], TestClient]) -> None:
    azure = _provider("azure", [ServiceResponseException("boom"), _reply(GOOD)])
    response = client_with([azure]).post("/ask", json={"question": "q"})
    assert response.json()["provider"] == "azure"
    assert SERVICES["azure"].await_count == 2


def test_ask_falls_back_after_retries(client_with: Callable[[list[Provider]], TestClient]) -> None:
    azure = _provider("azure", [ServiceResponseException("boom")] * 2)
    ollama = _provider("ollama", [_reply("not json"), _reply(GOOD)])
    response = client_with([azure, ollama]).post("/ask", json={"question": "q"})
    assert response.json()["provider"] == "ollama"
    assert SERVICES["azure"].await_count == 2
    assert SERVICES["ollama"].await_count == 2


def test_ask_502_when_all_fail(client_with: Callable[[list[Provider]], TestClient]) -> None:
    providers = [_provider("azure", [_reply(None)] * 2), _provider("ollama", [_reply('{"answer": 1}')] * 2)]
    assert client_with(providers).post("/ask", json={"question": "q"}).status_code == 502


def test_ask_requires_key_outside_local(client_with: Callable[[list[Provider]], TestClient]) -> None:
    client = client_with([_provider("azure", [_reply(GOOD)] * 2)])
    app.dependency_overrides[get_settings] = lambda: Settings(environment="prod", api_key="secret")
    assert client.post("/ask", json={"question": "q"}).status_code == 401
    assert client.post("/ask", json={"question": "q"}, headers={"X-API-Key": "nope"}).status_code == 401
    assert client.post("/ask", json={"question": "q"}, headers={"X-API-Key": "secret"}).status_code == 200


def test_ask_rejects_extra_fields(client_with: Callable[[list[Provider]], TestClient]) -> None:
    client = client_with([_provider("azure", [])])
    assert client.post("/ask", json={"question": "q", "system": "x"}).status_code == 422


def test_security_headers(client_with: Callable[[list[Provider]], TestClient]) -> None:
    headers = client_with([_provider("azure", [])]).get("/status").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["cache-control"] == "no-store"


def test_azure_auth_depends_on_environment() -> None:
    cases: list[tuple[Literal["local", "dev"], str, bool]] = [
        ("local", "k", True),
        ("dev", "k", False),
        ("local", "", False),
    ]
    for env, key, expect_key in cases:
        settings = Settings(
            _env_file=None,
            environment=env,
            azure_openai_api_key=key,
            azure_openai_endpoint="https://x.openai.azure.com/",
            azure_openai_deployment="d",
        )
        with patch.object(client, "AzureChatCompletion") as azure, patch.object(client, "DefaultAzureCredential"):
            client.build_kernel(settings)
        assert (azure.call_args.kwargs["api_key"] == "k") is expect_key
        assert (azure.call_args.kwargs["credential"] is None) is expect_key


def test_telemetry_is_noop_without_connection_string() -> None:
    with patch.object(telemetry, "configure_azure_monitor") as configure:
        telemetry.setup_telemetry(Settings(_env_file=None), app)
    configure.assert_not_called()


def test_telemetry_configures_azure_monitor_with_resource() -> None:
    settings = Settings(
        _env_file=None,
        applicationinsights_connection_string="InstrumentationKey=x",
        environment="uat",
        app_version="1.2.3",
    )
    with (
        patch.object(telemetry, "configure_azure_monitor") as configure,
        patch.object(telemetry, "FastAPIInstrumentor"),
    ):
        telemetry.setup_telemetry(settings, app)
    attributes = configure.call_args.kwargs["resource"].attributes
    assert attributes["service.version"] == "1.2.3"
    assert attributes["deployment.environment"] == "uat"


@pytest.mark.parametrize("log_content", [False, True])
def test_llm_completed_log_has_debug_fields(caplog: pytest.LogCaptureFixture, log_content: bool) -> None:
    llm = LLMClient(
        _kernel(), [_provider("azure", [_reply(GOOD)])], Settings(_env_file=None, log_llm_content=log_content)
    )
    app.dependency_overrides[get_llm_client] = lambda: llm
    with caplog.at_level(logging.INFO, logger="llm.client"):
        TestClient(app).post("/ask", json={"question": "q"})
    app.dependency_overrides.clear()
    record = next(r for r in caplog.records if r.message == "llm.completed")
    assert (record.input_tokens, record.output_tokens) == (5, 7)  # type: ignore[attr-defined]
    assert record.latency_ms >= 0 and record.attempt == 1 and record.model == "azure-model"  # type: ignore[attr-defined]
    assert hasattr(record, "input") is log_content
    assert hasattr(record, "output") is log_content


def test_failed_attempt_is_logged_with_error_and_output(caplog: pytest.LogCaptureFixture) -> None:
    llm = LLMClient(_kernel(), [_provider("azure", [_reply("not json")])], Settings(_env_file=None, llm_max_attempts=1))
    with caplog.at_level(logging.INFO, logger="llm.client"), pytest.raises(LLMUnavailableError):
        asyncio.run(llm.complete_json("q", Answer))
    record = next(r for r in caplog.records if r.message == "llm.attempt_failed")
    assert record.error_type == "ValidationError"  # type: ignore[attr-defined]
    assert record.output == "not json"  # type: ignore[attr-defined]
    assert record.latency_ms >= 0 and record.attempt == 1 and record.prompt_version == "1.1.0"  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("environment", "explicit", "expected"),
    [
        ("local", None, True),
        ("dev", None, True),
        ("uat", None, False),
        ("prod", None, False),
        ("prod", True, True),
        ("dev", False, False),
    ],
)
def test_llm_content_logging_default_by_environment(
    environment: Literal["local", "dev", "uat", "prod"], explicit: bool | None, expected: bool
) -> None:
    settings = Settings(_env_file=None, environment=environment, log_llm_content=explicit)
    assert settings.should_log_llm_content is expected


def test_empty_env_values_mean_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LOG_LLM_CONTENT", "APPLICATIONINSIGHTS_CONNECTION_STRING", "AZURE_OPENAI_API_KEY"):
        monkeypatch.setenv(name, "")
    settings = Settings(_env_file=None, environment="prod")
    assert settings.log_llm_content is None
    assert settings.should_log_llm_content is False


def test_root_redirects_to_docs_in_local(client_with: Callable[[list[Provider]], TestClient]) -> None:
    response = client_with([_provider("azure", [])]).get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


@pytest.mark.parametrize("error", [OpenAIError("Missing credentials."), ClientAuthenticationError("no login")])
def test_credential_errors_fall_back_instead_of_failing(
    client_with: Callable[[list[Provider]], TestClient], error: Exception
) -> None:
    azure = _provider("azure", [error] * 2)
    ollama = _provider("ollama", [_reply(GOOD)])
    response = client_with([azure, ollama]).post("/ask", json={"question": "q"})
    assert response.status_code == 200
    assert response.json()["provider"] == "ollama"
