"""Writing runs and the index the dashboard lists."""

import json
from pathlib import Path

from evals.records import Run


def write_run(results_dir: Path, run: Run) -> Path:
    """Write `runs/<run_id>.json` and rebuild `index.json`.

    Args:
        results_dir: The `results/` folder (served by the dashboard).
        run: The finished run.

    Returns:
        Path of the run file.
    """
    runs_dir = results_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{run.run_id}.json"
    path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
    rebuild_index(results_dir)
    return path


def rebuild_index(results_dir: Path) -> None:
    """List every run, newest first, with the fields the dashboard needs before loading one."""
    entries = []
    for file in (results_dir / "runs").glob("*.json"):
        data = json.loads(file.read_text(encoding="utf-8"))
        entries.append(
            {
                "run_id": data["run_id"],
                "label": data["label"],
                "created_at": data["created_at"],
                "git_commit": data["git_commit"],
                "variants": [v["id"] for v in data["variants"]],
                "cases": len({r["case_id"] for r in data["rows"]}),
            }
        )
    entries.sort(key=lambda e: e["created_at"], reverse=True)
    (results_dir / "index.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
