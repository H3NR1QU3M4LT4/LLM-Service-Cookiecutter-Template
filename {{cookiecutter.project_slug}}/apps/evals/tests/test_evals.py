import json
from pathlib import Path
from unittest.mock import patch

import pytest
from llm.client import Completion, LLMUnavailableError
from models.llm import Answer

from evals import runner
from evals.checks import run_checks
from evals.dataset import load_cases
from evals.pricing import estimate_cost, load_prices
from evals.records import Case, Verdict
from evals.results import rebuild_index, write_run
from evals.runner import RunConfig, parse_model_spec, resolve_prompt, run_matrix


def test_checks() -> None:
    case = Case(id="c", question="q", must_contain=["Lisbon"], must_not_contain=["secret"])
    assert run_checks(case, "It is LISBON.") == {"answered": True, "contains:Lisbon": True, "not_contains:secret": True}
    assert run_checks(case, None)["answered"] is False
    assert run_checks(case, "the secret")["not_contains:secret"] is False


def test_dataset_rejects_duplicate_ids(tmp_path: Path) -> None:
    file = tmp_path / "d.jsonl"
    file.write_text('{"id": "a", "question": "q"}\n{"id": "a", "question": "q2"}\n')
    with pytest.raises(ValueError, match="Duplicate"):
        load_cases(file)


def test_dataset_hash_changes_with_content(tmp_path: Path) -> None:
    file = tmp_path / "d.jsonl"
    file.write_text('{"id": "a", "question": "q"}\n')
    _, first = load_cases(file)
    file.write_text('{"id": "a", "question": "q2"}\n')
    assert load_cases(file)[1] != first


def test_pricing(tmp_path: Path) -> None:
    file = tmp_path / "p.yaml"
    file.write_text('"azure:m":\n  input_per_1m: 2.0\n  output_per_1m: 10.0\n')
    prices = load_prices(file)
    assert estimate_cost(prices, "azure:m", 1000, 500) == pytest.approx(0.007)
    assert estimate_cost(prices, "azure:other", 1000, 500) is None
    assert estimate_cost(prices, "azure:m", None, 500) is None
    assert load_prices(tmp_path / "missing.yaml") == {}


def test_model_spec() -> None:
    assert parse_model_spec("ollama:gemma4:e2b") == ("ollama", "gemma4:e2b")
    with pytest.raises(ValueError, match="Model must look like"):
        parse_model_spec("gpt-4")


def test_resolve_prompt_working_tree() -> None:
    prompt = resolve_prompt("ask")
    assert prompt.name == "ask"
    assert prompt.version


class FakeClient:
    def __init__(self, answers: dict[str, str | None], verdict: Verdict | None = None) -> None:
        self.answers = answers
        self.verdict = verdict

    async def complete(self, prompt: str, schema: type, **_: object) -> Completion:  # type: ignore[type-arg]
        if schema is Verdict:
            if self.verdict is None:
                raise LLMUnavailableError
            return Completion(self.verdict, "azure", "judge", "judge", "1.0.0", 1, 5, 1, 1)
        answer = self.answers[prompt]
        if answer is None:
            raise LLMUnavailableError
        return Completion(Answer(answer=answer, confidence=0.9), "ollama", "m", "ask", "1.0.0", 1, 120, 10, 20)


async def test_run_matrix_records_checks_judge_cost_and_errors(tmp_path: Path) -> None:
    dataset = tmp_path / "d.jsonl"
    dataset.write_text(
        '{"id": "ok", "question": "capital?", "must_contain": ["Lisbon"]}\n'
        '{"id": "bad", "question": "broken?"}\n'
        '{"id": "wrong", "question": "wrong?", "must_contain": ["Lisbon"]}\n'
    )
    prices = tmp_path / "prices.yaml"
    prices.write_text('"ollama:m":\n  input_per_1m: 1000000.0\n  output_per_1m: 1000000.0\n')
    clients = {
        "ollama:m": FakeClient({"capital?": "Lisbon", "broken?": None, "wrong?": "Madrid"}),
        "azure:judge": FakeClient({}, Verdict(score=4, reason="fine")),
    }
    config = RunConfig(
        models=["ollama:m"], judge="azure:judge", dataset=dataset, prices_path=prices, results_dir=tmp_path / "res"
    )
    with patch.object(runner, "make_client", lambda spec, _timeout: clients[spec]):
        run = await run_matrix(config)

    rows = {r.case_id: r for r in run.rows}
    assert rows["ok"].passed and rows["ok"].judge_score == 4 and rows["ok"].latency_ms == 120
    assert rows["ok"].cost_usd == pytest.approx(30.0)
    assert rows["bad"].error and not rows["bad"].passed and rows["bad"].judge_score is None
    assert not rows["wrong"].passed
    assert run.judge == {"model": "azure:judge", "prompt_version": "1.0.0"}
    assert len(run.variants) == 1 and run.dataset["cases"] == 3

    path = write_run(tmp_path / "res", run)
    assert json.loads(path.read_text())["run_id"] == run.run_id
    index = json.loads((tmp_path / "res" / "index.json").read_text())
    assert index[0]["run_id"] == run.run_id and index[0]["cases"] == 3


def test_index_is_newest_first(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    for run_id, created in [("a", "2026-01-01T00:00:00"), ("b", "2026-02-01T00:00:00")]:
        (runs / f"{run_id}.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "label": run_id,
                    "created_at": created,
                    "git_commit": None,
                    "variants": [],
                    "rows": [],
                }
            )
        )
    rebuild_index(tmp_path)
    assert [e["run_id"] for e in json.loads((tmp_path / "index.json").read_text())] == ["b", "a"]
