# Evals

Offline evals: run a dataset through several **models** and **prompt versions**, check and judge every answer, and
compare latency, tokens, cost and quality in a dashboard. A local tool: it is not deployed and not part of the backend
image. See [docs/evals.md](../../docs/evals.md) for the method.

## Run

```bash
cd apps/evals
cp .env.example .env                  # same provider settings as apps/backend/.env (Azure endpoint, Ollama host)
uv sync

# Models: azure:<deployment> or ollama:<model>. Prompts: ask (working tree) or ask@<git-ref>.
uv run python -m evals run \
  --models azure:chat ollama:gemma4:e2b \
  --prompts ask ask@main \
  --judge azure:chat \
  --label my-experiment

cd dashboard && npm install && cd ..  # once
uv run python -m evals dashboard      # http://localhost:5173
```

Each run writes `results/runs/<run_id>.json` and rebuilds `results/index.json` (git-ignored). The dashboard serves
that folder directly: no API. `EVALS_RESULTS_DIR=/path npm run dev` in `dashboard/` points it elsewhere.

## What is measured

Per row (one case on one variant): the answer or the error, deterministic checks (`must_contain`,
`must_not_contain`), the judge score (1-5) and reason, latency, input/output tokens and estimated cost. A variant is
`model | prompt@version`. Every call goes through the backend's `LLMClient` with a single provider (no fallback, no
retries), so a failure is recorded, not hidden.

## Files

| Path | What |
|---|---|
| `data/cases.jsonl` | Dataset: `id`, `question`, optional `reference`, `must_contain`, `must_not_contain`, `tags` |
| `prompts/judge.yaml` | Judge rubric; bump `version` when it changes, scores across judge versions are not comparable |
| `pricing.yaml` | USD per 1M tokens per `provider:model`, for cost estimates (fill in) |
| `evals/` | Runner, judge, checks, records, results writer, CLI (reuses `apps/backend/src`) |
| `dashboard/` | React + Vite + Tailwind: Comparison, Cases and History views |
| `tests/` | pytest with the LLM faked |

`evals/_backend.py` puts `apps/backend/src` on `sys.path`; backend and evals share code, not a package.
