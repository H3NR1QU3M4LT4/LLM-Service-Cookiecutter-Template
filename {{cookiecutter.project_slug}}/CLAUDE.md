# CLAUDE.md

{{ cookiecutter.project_description }}. {% if cookiecutter.app_type == "fastapi" %}FastAPI{% else %}Azure Functions (v2 model){% endif %} service on the shared `ai-utils` package.

## Commands

- `make sync` / `make check` (ruff, mypy strict, pytest) / `make run` / `make eval`

## Rules

- Business logic lives in `src/{{ cookiecutter.package_name }}/service.py`; the HTTP layer only validates and delegates.
- Before writing LLM, file-parsing, OCR, blob, chunking, search, RAG or eval code, check `docs/AI_UTILS.md`:
  ai-utils probably has it (add the extra instead of re-implementing).
- Use `ai_utils` for LLM calls (`LLMClient`), logging/tracing, chunking, search and evaluation. Generic helpers
  that a second project would need go to ai-utils, not here.
- Tests mock Azure SDKs; they must pass with no Azure credentials.
- Auth: `ENVIRONMENT=local` uses API keys from `.env`; anything else uses Entra ID. Never commit `.env`.
- Change the prompt or model? Run `make eval` before and after and compare `evals/results/scores.json`.
