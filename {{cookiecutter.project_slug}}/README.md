# {{ cookiecutter.project_name }}

{{ cookiecutter.project_description }}.

## Setup

```bash
cp .env.example .env   # fill in endpoints; ENVIRONMENT=local uses API keys, otherwise Entra ID (az login)
make sync              # uv sync + pre-commit hooks
make check             # ruff, mypy, pytest
make run               # {% if cookiecutter.app_type == "fastapi" %}uvicorn on http://127.0.0.1:8000 (POST /ask {"question": "..."}){% else %}func start (needs Azure Functions Core Tools and Azurite){% endif %}
make docker-build && make docker-run   # same app in a container, configured from .env
```
{% if cookiecutter.app_type == "azure-function" %}
Copy `local.settings.example.json` to `local.settings.json` for `func start`. Azure Functions installs from
`requirements.txt`, which `make requirements` exports from `uv.lock` (ai-utils is installed from its public
git tag, so remote build needs no credentials).
{% endif %}
## CI

`.github/workflows/ci.yml` runs on every pull request: the same pre-commit hooks as local commits
(file checks, gitleaks, ruff, mypy, pylint), pytest, and a Docker build. Mark the `quality` and `docker` checks
as required in the repository's branch protection.

## Layout

| Path | What |
|---|---|
| `src/{{ cookiecutter.package_name }}/service.py` | Core logic on `ai_utils.llm.LLMClient` |
{%- if cookiecutter.app_type == "fastapi" %}
| `src/{{ cookiecutter.package_name }}/api.py` | FastAPI app |
{%- else %}
| `function_app.py` | Azure Functions HTTP triggers |
{%- endif %}
{%- if cookiecutter.include_agent == "y" %}
| `src/{{ cookiecutter.package_name }}/agent.py` | Foundry prompt agent: `make agent-deploy`, then `uv run python -m {{ cookiecutter.package_name }}.agent ask "..."` |
{%- endif %}
| `evals/` | `make eval`: scores `data.jsonl` with relevance, similarity and a rubric judge |

## Shared code

[`docs/AI_UTILS.md`](docs/AI_UTILS.md) shows how to use every ai-utils tool (LLM, file preprocessing and OCR,
Blob, chunking, Search/RAG, evaluation, monitoring) with the extra each one needs.


Generic LLM, RAG, search and evaluation code belongs in [ai-utils]({{ cookiecutter.ai_utils_git }}), pinned in
`pyproject.toml` (`[tool.uv.sources]`). To work on both at once, point the source at a local checkout:
`ai-utils = { path = "../ai-utils", editable = true }`.
