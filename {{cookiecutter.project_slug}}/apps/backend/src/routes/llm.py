"""LLM route."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from llm.client import LLMClient, LLMUnavailableError
from models.llm import Answer, AskRequest, AskResponse
from routes.deps import get_llm_client

router = APIRouter()


@router.post("/ask")
async def ask(request: AskRequest, llm: Annotated[LLMClient, Depends(get_llm_client)]) -> AskResponse:
    """Answer a question with a JSON-validated LLM response."""
    try:
        result, provider = await llm.complete_json(request.question, Answer)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AskResponse(result=result, provider=provider)
