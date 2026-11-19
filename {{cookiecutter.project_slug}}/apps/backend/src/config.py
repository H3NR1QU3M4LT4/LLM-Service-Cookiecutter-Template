"""Application settings, read from environment variables and `.env`."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Azure is the primary provider; Ollama is the fallback."""

    # env_ignore_empty: `LOG_LLM_CONTENT=` in .env.example must mean "unset", not an unparsable empty string.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    environment: Literal["local", "dev", "uat", "prod"] = "local"
    # Injected at build/deploy time (e.g. from the git tag); shown on /status and in the OpenAPI doc.
    app_version: str = "0.0.1"
    # Required on /ask (X-API-Key header). Empty is only accepted when environment is "local".
    api_key: str = ""
    # Exact frontend origins allowed by CORS; empty disables CORS.
    cors_origins: list[str] = []

    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-10-21"
    # Only used when environment is "local"; everywhere else (or when empty) Entra ID (DefaultAzureCredential).
    azure_openai_api_key: str = ""

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen3-coder:30b"

    # Empty disables telemetry. Standard Azure name, also set automatically by Azure hosting.
    applicationinsights_connection_string: str = ""
    log_level: str = "INFO"
    # Log the question and the raw LLM output (truncated to 2000 chars) to debug prompts. They can contain personal
    # data, so unset means on only in local and dev; set it explicitly to override.
    log_llm_content: bool | None = None

    # Attempts per provider before falling back to the next one.
    llm_max_attempts: int = 3
    # Per attempt; a stuck provider must not hold a worker.
    llm_timeout_seconds: float = 30.0
    llm_retry_min_wait_seconds: float = 1.0
    llm_retry_max_wait_seconds: float = 10.0

    @property
    def should_log_llm_content(self) -> bool:
        """Whether to log the question and raw LLM output."""
        if self.log_llm_content is None:
            return self.environment in ("local", "dev")
        return self.log_llm_content


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings."""
    return Settings()
