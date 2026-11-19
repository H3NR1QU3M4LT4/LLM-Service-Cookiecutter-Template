# {{ cookiecutter.project_name }}

{{ cookiecutter.project_description }}.

A FastAPI backend that asks an LLM through Semantic Kernel (Azure OpenAI / Foundry first, Ollama as fallback, retry
with backoff, validated JSON answers, versioned prompts) and a React frontend, with Application Insights telemetry
and Terraform for Azure.

## Layout

| Path | What |
|---|---|
| [`apps/backend`](apps/backend/README.md) | FastAPI + Semantic Kernel API: `/status`, `/ask` |
| [`apps/frontend`](apps/frontend/README.md) | React + Vite + Tailwind UI served by nginx, which proxies `/api/` and adds the API key |
| [`apps/evals`](apps/evals/README.md) | Offline evals (Python runner + React dashboard): compare models and prompt versions on latency, tokens, cost and judge score |
| [`infra/`](docs/infrastructure.md) | Terragrunt + Terraform for `dev`, `uat` and `prod`: two Docker web apps, container registry, Foundry model, Application Insights, budget alerts at 80%, dashboard |
| [`docs/`](docs/README.md) | Observability, infrastructure and prompt versioning |
| `docker-compose.yml` | Backend and frontend together, locally |
| `.pre-commit-config.yaml`, `.github/workflows/ci.yml` | Quality gates, identical locally and in CI |

## Run everything locally

```bash
cp apps/backend/.env.example apps/backend/.env    # the one config file: API_KEY, ENVIRONMENT, APP_VERSION, LLM endpoints...
docker compose up --build                         # http://localhost:8080
```

The lockfiles (`apps/backend/uv.lock`, `apps/evals/uv.lock`) are created when the project is generated; if `uv` was missing then, run
`uv lock` in both. Without Docker, see each app's README (`uvicorn` on :8000 and `npm run dev` on :5173).

## Quality

`.pre-commit-config.yaml` runs, on commit: file checks, gitleaks, conventional commit messages, `ruff check`,
`ruff format`, `mypy` (strict), `pylint`. On push: `uv sync`, `pytest`, coverage >= 80%, and the frontend
type-check and build. After a checkout or merge it re-syncs dependencies.

```bash
uv tool install pre-commit
pre-commit install --install-hooks -t pre-commit -t pre-push -t commit-msg -t post-checkout -t post-merge
```

`.github/workflows/ci.yml` runs the same hooks on every pull request (plus gitleaks over the full history) and builds
both Docker images. Mark the `quality` and `docker` checks as required in the repository's branch protection.

## Deploy to Azure

Each environment is a folder under `infra/live/` (`dev`, `uat`, `prod`); run it locally with Terragrunt or from the
"Infrastructure - Terragrunt" GitHub Action (plan, then approved apply). Follow
[docs/infrastructure.md](docs/infrastructure.md) and read its "Not covered" section first: the backend is
reachable from the internet and protected only by the API key until you add login and network restrictions.

## Observability and prompts

- [docs/observability.md](docs/observability.md): what is logged per LLM call (provider, model, prompt version, tokens,
  latency, errors), the dashboard and example queries.
- [docs/prompt-versioning.md](docs/prompt-versioning.md): prompts are files in git, versioned and guarded by a test.
- [docs/evals.md](docs/evals.md): choose models and prompt versions with a dataset, checks and an LLM judge.
- [docs/frontend-ui.md](docs/frontend-ui.md): both frontends share the Leica logo, navbar, footer and layout; a hook keeps them identical.
