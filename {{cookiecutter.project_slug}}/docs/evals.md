# Evals: choosing models and prompts

Use this while experimenting, before a model or prompt reaches `uat`. The dashboard in Application Insights
([observability.md](observability.md)) measures real traffic; evals decide *which variant* to ship.

## The unit of comparison

A **variant** is a model plus a prompt version: `azure:chat | ask@1.1.0`. A **run** executes every case of a dataset on
every variant and records, per row: answer or error, checks, judge score, latency, tokens, cost. Runs also record the
dataset hash, the judge model and prompt version, the temperature and the git commit, so results stay comparable.

## Method

1. **Dataset in git** (`apps/evals/data/cases.jsonl`): 30 to 100 real cases, including hard ones, "I don't know" cases
   and prompt-injection attempts. Changing it changes its hash; compare runs only on the same hash.
2. **Deterministic checks first** (`must_contain`, `must_not_contain`): cheap and exact. They gate the judge's score.
3. **LLM-as-judge** with a written rubric (`prompts/judge.yaml`), temperature 0, a model different from (ideally
   stronger than) the one under test. Calibrate on 10 to 20 cases you graded yourself before trusting it; a judge you
   have not checked against a human is noise.
4. **Decide with a rule written beforehand**, for example: "switch model if judge improves by 0.3 and p95 latency does
   not worsen by more than 20%".

## Comparing prompt versions

Prompts are files in git (`apps/backend/src/prompts/*.yaml`, see [prompt-versioning.md](prompt-versioning.md)). The
runner reads `ask` from the working tree or `ask@<git-ref>` from any commit, branch or tag, so a new prompt is compared
with the old one without checking anything out:

```bash
uv run python -m evals run --models azure:chat --prompts ask@main ask --judge azure:strong --label tighter-rules
```

## Dashboard

- **Comparison**: one run, one row per variant, deltas against a baseline you pick (green = better): checks passed,
  errors, judge, latency p50/p95, tokens, cost.
- **Cases**: worst first, with the judge's reason; compare two variants side by side on the same case.
- **History**: the same variant across runs, with commit and dataset hash.

## Limits

- Judge scores depend on the judge model, rubric and prompt version. Keep them fixed across the runs you compare.
- Small datasets give noisy averages: look at the cases, not only the mean.
- Cost needs `pricing.yaml`; without a price a variant shows `–`.
- Not covered yet: repeated runs per case to measure variance, Foundry Evaluations integration, scoring of sampled
  production traffic. Add them when a decision needs them.
