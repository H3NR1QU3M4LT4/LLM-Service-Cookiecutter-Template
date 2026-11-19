"""Models for the LLM route."""

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    """Question sent by the client."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=4000)


class Answer(BaseModel):
    """JSON the LLM must produce."""

    answer: str = Field(description="Direct answer to the question.")
    confidence: float = Field(ge=0, le=1, description="Self-assessed confidence between 0 and 1.")


class AskResponse(BaseModel):
    """Validated LLM answer plus the provider that produced it."""

    result: Answer
    provider: str
