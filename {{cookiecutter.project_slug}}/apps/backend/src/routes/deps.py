"""Shared FastAPI dependencies."""

from functools import lru_cache

from config import get_settings
from llm.client import LLMClient, build_kernel


@lru_cache
def get_llm_client() -> LLMClient:
    """Return the process-wide LLM client."""
    settings = get_settings()
    kernel, providers = build_kernel(settings)
    return LLMClient(kernel, providers, settings)
