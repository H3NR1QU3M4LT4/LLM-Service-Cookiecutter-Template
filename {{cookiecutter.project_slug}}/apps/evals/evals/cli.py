"""Command line: `python -m evals run ...` and `python -m evals dashboard`."""

import argparse
import asyncio
import subprocess
from pathlib import Path

from evals.results import write_run
from evals.runner import RunConfig, run_matrix

_DASHBOARD = Path(__file__).resolve().parents[1] / "dashboard"


def _summary(run_rows: list[tuple[str, int, int, float | None]]) -> str:
    lines = [f"{'variant':60} {'cases':>5} {'passed':>6} {'judge':>6}"]
    for variant, cases, passed, judge in run_rows:
        lines.append(f"{variant:60} {cases:>5} {passed:>6} {'-' if judge is None else f'{judge:.2f}':>6}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(prog="evals")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run models x prompt versions over a dataset")
    run.add_argument("--models", nargs="+", required=True, help="azure:<deployment> or ollama:<model>")
    run.add_argument("--prompts", nargs="+", default=["ask"], help="ask (working tree) or ask@<git-ref>")
    run.add_argument("--judge", help="Judge model, e.g. azure:<deployment>; omit to skip the judge")
    run.add_argument("--dataset", type=Path, default=RunConfig.dataset)
    run.add_argument("--label", default="run")
    run.add_argument("--temperature", type=float, default=0.0)
    run.add_argument("--concurrency", type=int, default=4)

    sub.add_parser("dashboard", help="Open the results dashboard (needs npm install in dashboard/)")

    args = parser.parse_args(argv)
    if args.command == "dashboard":
        subprocess.run(["npm", "run", "dev"], cwd=_DASHBOARD, check=True)
        return

    config = RunConfig(
        models=args.models,
        prompts=args.prompts,
        judge=args.judge,
        dataset=args.dataset,
        label=args.label,
        temperature=args.temperature,
        concurrency=args.concurrency,
    )
    result = asyncio.run(run_matrix(config))
    path = write_run(config.results_dir, result)
    table = []
    for variant in result.variants:
        rows = [r for r in result.rows if r.variant == variant.id]
        scores = [r.judge_score for r in rows if r.judge_score is not None]
        table.append(
            (variant.id, len(rows), sum(r.passed for r in rows), sum(scores) / len(scores) if scores else None)
        )
    print(_summary(table))
    print(f"\nWrote {path}")
