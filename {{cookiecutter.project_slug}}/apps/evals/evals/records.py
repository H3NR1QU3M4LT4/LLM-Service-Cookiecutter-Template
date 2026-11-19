"""Data shapes: dataset cases, one result row per (variant, case), and the run file the dashboard reads."""

from pydantic import BaseModel, Field


class Case(BaseModel):
    """One dataset line (`data/*.jsonl`)."""

    id: str
    question: str
    reference: str | None = Field(default=None, description="Ideal answer, shown to the judge.")
    must_contain: list[str] = []
    must_not_contain: list[str] = []
    tags: list[str] = []


class Variant(BaseModel):
    """What is being compared: a model with a prompt version."""

    id: str
    provider: str
    model: str
    prompt: str
    prompt_version: str


class Verdict(BaseModel):
    """What the judge must answer."""

    score: int = Field(ge=1, le=5, description="1 (wrong or unsafe) to 5 (excellent).")
    reason: str = Field(description="One or two sentences justifying the score.")


class Row(BaseModel):
    """Result of one case on one variant."""

    variant: str
    case_id: str
    question: str
    output: str | None
    error: str | None
    checks: dict[str, bool]
    passed: bool
    judge_score: int | None
    judge_reason: str | None
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None


class Run(BaseModel):
    """One execution of the matrix, written to `results/runs/<run_id>.json`."""

    run_id: str
    label: str
    created_at: str
    git_commit: str | None
    git_dirty: bool
    dataset: dict[str, str | int]
    temperature: float
    judge: dict[str, str] | None
    variants: list[Variant]
    rows: list[Row]
