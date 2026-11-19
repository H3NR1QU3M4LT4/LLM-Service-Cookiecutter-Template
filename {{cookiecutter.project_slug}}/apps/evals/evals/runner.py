"""Run the (model x prompt version) matrix over a dataset, check, judge and record every call."""

import asyncio
import re
import subprocess
from collections.abc import Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import Settings
from llm.client import LLMClient, LLMUnavailableError, build_kernel
from llm.prompts import Prompt, load_prompt, parse_prompt
from models.llm import Answer

from evals.checks import run_checks
from evals.dataset import load_cases
from evals.pricing import estimate_cost, load_prices
from evals.records import Case, Row, Run, Variant, Verdict

_EVALS_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _EVALS_DIR.parents[1]
_BACKEND_PROMPTS = _EVALS_DIR.parent / "backend" / "src" / "prompts"


@dataclass
class RunConfig:
    """Everything one run needs."""

    models: list[str]
    prompts: list[str] = field(default_factory=lambda: ["ask"])
    judge: str | None = None
    dataset: Path = _EVALS_DIR / "data" / "cases.jsonl"
    label: str = "run"
    temperature: float = 0.0
    concurrency: int = 4
    timeout_seconds: float = 60.0
    results_dir: Path = _EVALS_DIR / "results"
    prices_path: Path = _EVALS_DIR / "pricing.yaml"
    judge_prompt_dir: Path = _EVALS_DIR / "prompts"


def parse_model_spec(spec: str) -> tuple[str, str]:
    """Split `azure:<deployment>` or `ollama:<model>` (the model may itself contain colons)."""
    provider, _, model = spec.partition(":")
    if provider not in ("azure", "ollama") or not model:
        raise ValueError(f"Model must look like azure:<deployment> or ollama:<model>, got {spec!r}.")
    return provider, model


def make_client(spec: str, timeout_seconds: float) -> LLMClient:
    """Build a client with exactly one provider, so a failure is recorded instead of hidden by the fallback."""
    provider_name, model = parse_model_spec(spec)
    overrides = {"azure_openai_deployment": model} if provider_name == "azure" else {"ollama_model": model}
    settings = Settings(llm_max_attempts=1, llm_timeout_seconds=timeout_seconds, **overrides)  # type: ignore[arg-type]
    kernel, providers = build_kernel(settings)
    chosen = [p for p in providers if p.name == provider_name]
    if not chosen:
        raise ValueError(f"Provider {provider_name!r} is not configured (check the .env, e.g. AZURE_OPENAI_ENDPOINT).")
    return LLMClient(kernel, chosen, settings)


def resolve_prompt(ref: str, repo_root: Path = _REPO_ROOT) -> Prompt:
    """Load a backend prompt: `ask` is the working tree, `ask@<git-ref>` is that file at a commit, branch or tag."""
    name, _, git_ref = ref.partition("@")
    if not git_ref:
        return load_prompt(name, _BACKEND_PROMPTS)
    path = (_BACKEND_PROMPTS / f"{name}.yaml").relative_to(repo_root)
    text = subprocess.run(
        ["git", "show", f"{git_ref}:{path.as_posix()}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return parse_prompt(text)


def git_state(repo_root: Path = _REPO_ROOT) -> tuple[str | None, bool]:
    """Return (short commit, has uncommitted changes); (None, False) outside a git repository."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return None, False
    return commit, dirty


async def _judge(client: LLMClient, prompt: Prompt, case: Case, output: str) -> Verdict | None:
    try:
        completion = await client.complete(
            case.question,
            Verdict,
            template=prompt,
            temperature=0.0,
            variables={"answer": output, "reference": case.reference or "(none)"},
        )
    except LLMUnavailableError:
        return None
    return completion.result


async def _run_case(
    client: LLMClient,
    variant: Variant,
    prompt: Prompt,
    case: Case,
    config: RunConfig,
    prices: dict[str, dict[str, float]],
    judge: tuple[LLMClient, Prompt] | None,
) -> Row:
    output: str | None = None
    error: str | None = None
    latency = in_tokens = out_tokens = None
    try:
        completion = await client.complete(case.question, Answer, template=prompt, temperature=config.temperature)
        output = completion.result.answer
        latency, in_tokens, out_tokens = completion.latency_ms, completion.input_tokens, completion.output_tokens
    except LLMUnavailableError:
        error = "LLMUnavailableError: the provider failed or returned an invalid answer"
    checks = run_checks(case, output)
    verdict = await _judge(judge[0], judge[1], case, output) if judge and output else None
    return Row(
        variant=variant.id,
        case_id=case.id,
        question=case.question,
        output=output,
        error=error,
        checks=checks,
        passed=all(checks.values()),
        judge_score=verdict.score if verdict else None,
        judge_reason=verdict.reason if verdict else None,
        latency_ms=latency,
        input_tokens=in_tokens,
        output_tokens=out_tokens,
        cost_usd=estimate_cost(prices, f"{variant.provider}:{variant.model}", in_tokens, out_tokens),
    )


async def run_matrix(config: RunConfig) -> Run:
    """Run every case on every (model, prompt) variant and return the finished run (not yet written to disk).

    Args:
        config: Models, prompt refs, optional judge, dataset and limits.

    Returns:
        The run with one row per (variant, case).
    """
    cases, dataset_sha = load_cases(config.dataset)
    prices = load_prices(config.prices_path)
    prompts = {ref: resolve_prompt(ref) for ref in config.prompts}
    clients = {spec: make_client(spec, config.timeout_seconds) for spec in config.models}
    judge = None
    judge_info = None
    if config.judge:
        judge_prompt = load_prompt("judge", config.judge_prompt_dir)
        judge = (make_client(config.judge, config.timeout_seconds), judge_prompt)
        judge_info = {"model": config.judge, "prompt_version": judge_prompt.version}

    variants: list[Variant] = []
    jobs: list[Coroutine[Any, Any, Row]] = []
    semaphore = asyncio.Semaphore(config.concurrency)

    async def limited(coro_args: tuple[LLMClient, Variant, Prompt, Case]) -> Row:
        async with semaphore:
            return await _run_case(*coro_args, config, prices, judge)

    for spec in config.models:
        provider, model = parse_model_spec(spec)
        for prompt in prompts.values():
            variant = Variant(
                id=f"{spec} | {prompt.name}@{prompt.version}",
                provider=provider,
                model=model,
                prompt=prompt.name,
                prompt_version=prompt.version,
            )
            variants.append(variant)
            jobs.extend(limited((clients[spec], variant, prompt, case)) for case in cases)

    rows = list(await asyncio.gather(*jobs))
    commit, dirty = git_state()
    now = datetime.now(UTC)
    slug = re.sub(r"[^a-z0-9]+", "-", config.label.lower()).strip("-") or "run"
    return Run(
        run_id=f"{now:%Y%m%d-%H%M%S}-{slug}",
        label=config.label,
        created_at=now.isoformat(timespec="seconds"),
        git_commit=commit,
        git_dirty=dirty,
        dataset={"path": config.dataset.name, "sha256": dataset_sha, "cases": len(cases)},
        temperature=config.temperature,
        judge=judge_info,
        variants=variants,
        rows=rows,
    )
