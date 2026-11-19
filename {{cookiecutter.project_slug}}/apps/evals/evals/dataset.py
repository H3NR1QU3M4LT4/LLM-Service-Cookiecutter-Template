"""Dataset loading."""

import hashlib
from pathlib import Path

from evals.records import Case


def load_cases(path: Path) -> tuple[list[Case], str]:
    """Read a JSONL dataset.

    Args:
        path: File with one JSON object per line.

    Returns:
        The cases and the SHA-256 of the file, so a run records which dataset version it used.
    """
    raw = path.read_bytes()
    cases = [Case.model_validate_json(line) for line in raw.decode().splitlines() if line.strip()]
    ids = [c.id for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate case ids in {path}.")
    return cases, hashlib.sha256(raw).hexdigest()[:12]
