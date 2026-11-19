# {{ cookiecutter.project_name }}

{{ cookiecutter.project_description }}.

FastAPI service that asks an LLM through Semantic Kernel and returns validated JSON. Azure OpenAI / Foundry is the
primary provider, Ollama the fallback. Each provider is retried with exponential backoff before falling back.

## Endpoints

| Route | Auth | What |
|---|---|---|
| `GET /status` | none | `status`, `service`, `version`, `environment` and the configured providers (no LLM call; used by the Docker healthcheck) |
| `POST /ask` | `X-API-Key` | `{"question": "..."}` returns `{"result": {"answer", "confidence"}, "provider": "azure"\|"ollama"}`; 502 when every provider fails |

`/docs` is only served when `ENVIRONMENT=local`.

## Run locally

```bash
cp .env.example .env     # fill in the Azure endpoint/deployment, or leave the endpoint empty to use only Ollama
uv sync
uv run uvicorn main:app --app-dir src --reload
curl localhost:8000/status
curl -X POST localhost:8000/ask -H 'Content-Type: application/json' -d '{"question": "Capital of Portugal?"}'
```

Tests: `uv run pytest`. Lint: `uv run ruff check . && uv run mypy`.

## Configuration

Environment variables or `.env` (see `.env.example`).

| Variable | Default | Meaning |
|---|---|---|
| `ENVIRONMENT` | `local` | `local`, `dev`, `uat` or `prod`. Anything but `local` requires `API_KEY` and disables `/docs` |
| `APP_VERSION` | `0.0.1` | Shown on `/status` and in OpenAPI; set it from CI (e.g. the git tag) |
| `API_KEY` | empty | Expected in the `X-API-Key` header of `/ask` |
| `CORS_ORIGINS` | `[]` | JSON list of exact frontend origins; empty disables CORS |
| `AZURE_OPENAI_ENDPOINT` / `_DEPLOYMENT` / `_API_VERSION` | empty / empty / `2024-10-21` | Primary provider; empty endpoint skips it |
| `AZURE_OPENAI_API_KEY` | empty | Used only when `ENVIRONMENT=local`; dev/uat/prod always use Entra ID (`DefaultAzureCredential`: managed identity in Azure) |
| `OLLAMA_HOST` / `OLLAMA_MODEL` | `http://localhost:11434` / `qwen3-coder:30b` | Fallback provider |
| `LLM_MAX_ATTEMPTS` | `3` | Attempts per provider before falling back |
| `LLM_TIMEOUT_SECONDS` | `30` | Timeout per attempt |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | empty | Exports logs, traces and requests to Application Insights; empty disables it |
| `LOG_LEVEL` | `INFO` | Root log level |
| `LOG_LLM_CONTENT` | unset | Log the question and raw LLM output (2000 chars max). Unset: on for `local`/`dev`, off for `uat`/`prod` |

## Observability

Every LLM call logs `llm.completed` or `llm.attempt_failed` with `provider`, `model`, `prompt`, `prompt_version`,
`attempt`, `latency_ms`, `input_tokens`, `output_tokens` and, when `LOG_LLM_CONTENT` is on, `input` and `output`.
Prompts live in `src/prompts/*.yaml`; changing a template requires bumping its `version` (`tests/test_prompts.py`).

## Docker

`uv.lock` must exist (the build uses `--frozen`): run `uv lock` once and commit it.

```bash
docker build --build-arg APP_VERSION=1.0.0 -t {{ cookiecutter.project_slug }} .
docker run --env-file .env -e ENVIRONMENT=dev -e API_KEY=change-me -p 8000:8000 {{ cookiecutter.project_slug }}
```

The image defaults to `ENVIRONMENT=prod`, so it refuses `/ask` until `API_KEY` is set. Inside a container
`localhost` is the container: point `OLLAMA_HOST` at `http://host.docker.internal:11434` to reach Ollama on your Mac.

## Layout

| Path | What |
|---|---|
| `src/main.py` | App, CORS, docs toggle, routers |
| `src/config.py` | Settings |
| `src/security.py` | API key dependency and security headers |
| `src/models/` | Request/response models (`status.py`, `llm.py`) |
| `src/routes/` | `status.py`, `llm.py`, `deps.py` |
| `src/llm/client.py` | Semantic Kernel kernel, providers, retry and fallback |
| `tests/` | pytest with the kernel mocked |

## Not covered

Rate limiting (do it at the gateway or reverse proxy), per-resource authorization and tenant isolation (no resources
yet), OAuth/Entra ID for callers (only an API key).
