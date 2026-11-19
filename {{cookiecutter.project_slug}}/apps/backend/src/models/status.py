"""Models for the status route."""

from typing import Literal

from pydantic import BaseModel


class ProviderStatus(BaseModel):
    """One configured LLM provider."""

    name: str
    model: str
    role: Literal["primary", "fallback"]


class StatusResponse(BaseModel):
    """Service status."""

    status: Literal["ok"]
    service: str
    version: str
    environment: Literal["local", "dev", "uat", "prod"]
    providers: list[ProviderStatus]
    prompts: dict[str, str]
