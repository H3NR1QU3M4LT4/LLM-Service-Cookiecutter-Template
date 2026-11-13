"""HTTP API."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from {{ cookiecutter.package_name }}.service import answer

app = FastAPI(title="{{ cookiecutter.project_name }}")


class AskRequest(BaseModel):
    """Question sent by the client."""

    question: str = Field(min_length=1, max_length=4000)


class AskResponse(BaseModel):
    """Answer returned to the client."""

    answer: str


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/ask")
async def ask(request: AskRequest) -> AskResponse:
    """Answer a question."""
    return AskResponse(answer=await answer(request.question))
