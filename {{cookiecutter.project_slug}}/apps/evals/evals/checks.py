"""Deterministic checks: cheap, exact, run before the judge."""

from evals.records import Case


def run_checks(case: Case, output: str | None) -> dict[str, bool]:
    """Evaluate a case's `must_contain` and `must_not_contain` against the answer text (case-insensitive).

    Args:
        case: The dataset case.
        output: The answer text, None when the call failed.

    Returns:
        Check name to pass/fail. `answered` is False when there is no output.
    """
    results = {"answered": bool(output)}
    text = (output or "").lower()
    for needle in case.must_contain:
        results[f"contains:{needle}"] = needle.lower() in text
    for needle in case.must_not_contain:
        results[f"not_contains:{needle}"] = needle.lower() not in text
    return results
