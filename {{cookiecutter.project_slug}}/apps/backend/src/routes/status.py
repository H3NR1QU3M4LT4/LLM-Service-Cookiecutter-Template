"""Status route."""

from typing import Annotated

from fastapi import APIRouter, Depends

from config import Settings, get_settings
from llm.client import PROMPT_VERSIONS, LLMClient
from models.status import ProviderStatus, StatusResponse
from routes.deps import get_llm_client

router = APIRouter()


@router.get("/status")
async def status(
    settings: Annotated[Settings, Depends(get_settings)], llm: Annotated[LLMClient, Depends(get_llm_client)]
) -> StatusResponse:
    """Report liveness, environment and the configured LLM providers (no provider call is made)."""
    return StatusResponse(
        status="ok",
        service="{{ cookiecutter.project_slug }}",
        version=settings.app_version,
        environment=settings.environment,
        providers=[
            ProviderStatus(name=p.name, model=p.model, role="primary" if i == 0 else "fallback")
            for i, p in enumerate(llm.providers)
        ],
        prompts=PROMPT_VERSIONS,
    )
