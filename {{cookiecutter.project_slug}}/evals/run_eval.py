"""Run `evals/data.jsonl` through the {% if cookiecutter.include_agent == "y" %}agent{% else %}service{% endif %} and score the answers.

Responses are generated first and written to `evals/results/responses.jsonl`, then scored by
`azure-ai-evaluation`. Generating up front (instead of passing `target=` to `evaluate`) keeps our async
client on a single event loop; `evaluate` runs targets from worker threads.

Each data row needs `query`; `ground_truth` enables the similarity score. Add `context` to rows and a
`GroundednessEvaluator` once the {% if cookiecutter.include_agent == "y" %}agent{% else %}service{% endif %} retrieves documents.

Scores are also logged to Application Insights (when `APPLICATION_INSIGHTS_CONNECTION_STRING` is set) under
`EVAL_RUN_NAME`, so the ai-utils observability workbook can compare runs.

Usage:
    EVAL_RUN_NAME=prompt-v2 python -m evals.run_eval
"""

{% if cookiecutter.include_agent != "y" %}import asyncio
{% endif %}import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_utils.core.telemetry import setup_logging, setup_tracing
from ai_utils.evaluation import RubricJudge, log_evaluation, model_config_from_env
from azure.ai.evaluation import RelevanceEvaluator, SimilarityEvaluator, evaluate

{% if cookiecutter.include_agent == "y" -%}
from {{ cookiecutter.package_name }}.agent import AGENT_NAME, ask, get_project_client
{%- else -%}
from {{ cookiecutter.package_name }}.service import answer
{%- endif %}

EVALS_DIR = Path(__file__).parent
DATA = EVALS_DIR / "data.jsonl"
RESULTS = EVALS_DIR / "results"
RUBRIC = "Answers the question directly and correctly, without padding or unsupported claims."


def load_rows(path: Path) -> list[dict[str, Any]]:
    """Read one JSON object per non-empty line."""
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


{% if cookiecutter.include_agent == "y" -%}
def generate_responses(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ask the deployed agent every query, sequentially (each call may involve several tool rounds)."""
    with get_project_client() as project, project.get_openai_client(agent_name=AGENT_NAME) as openai_client:
        return [{**row, "response": ask(openai_client, row["query"])} for row in rows]
{%- else -%}
async def generate_responses(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Answer every query concurrently (bounded by the LLM client's concurrency limit)."""
    answers = await asyncio.gather(*(answer(row["query"]) for row in rows))
    return [{**row, "response": response} for row, response in zip(rows, answers, strict=True)]
{%- endif %}


def main() -> None:
    """Generate responses, score them, and print the aggregate metrics."""
    RESULTS.mkdir(exist_ok=True)
    responses_path = RESULTS / "responses.jsonl"
    {% if cookiecutter.include_agent == "y" -%}
    rows = generate_responses(load_rows(DATA))
    {%- else -%}
    rows = asyncio.run(generate_responses(load_rows(DATA)))
    {%- endif %}
    responses_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))

    config = model_config_from_env()
    result = evaluate(
        data=str(responses_path),
        evaluators={
            "relevance": RelevanceEvaluator(config),
            "similarity": SimilarityEvaluator(config),
            "rubric": RubricJudge(RUBRIC),
        },
        output_path=str(RESULTS / "scores.json"),
    )
    service = "{{ cookiecutter.project_slug }}-eval"
    setup_tracing(service)
    run_name = os.environ.get("EVAL_RUN_NAME") or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log_evaluation(result, run_name=run_name, logger=setup_logging(service))
    print(run_name, json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
