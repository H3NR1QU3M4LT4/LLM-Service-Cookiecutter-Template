"""Core logic, kept independent of the HTTP layer so tests and evals call it directly."""

from functools import cache

from ai_utils.core.telemetry import setup_logging, setup_tracing
from ai_utils.llm import LLMClient, TextResponse

SERVICE_NAME = "{{ cookiecutter.project_slug }}"
SYSTEM_MESSAGE = "You are a concise, accurate assistant. Say so when you do not know the answer."


@cache
def get_llm_client() -> LLMClient:
    """Return the process-wide LLM client, created on first use so imports need no Azure config."""
    return LLMClient(logger=setup_logging(SERVICE_NAME), tracer=setup_tracing(SERVICE_NAME))


async def answer(question: str) -> str:
    """Answer a user question.

    Args:
        question: The user's question.

    Returns:
        The model's answer.
    """
    response = await get_llm_client().complete(question, TextResponse, system_message=SYSTEM_MESSAGE)
    return response.answer
