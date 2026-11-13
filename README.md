# LLM Service Cookiecutter Template

A single-package LLM service (FastAPI or Azure Function) built on
[ai-utils](https://github.com/H3NR1QU3M4LT4/ai-utils), with evaluation and an optional Foundry agent.
Use it for the many small services; use [llm-monorepo](../llm-monorepo) when you need several apps and
Terragrunt infrastructure.

## Generate

```bash
uvx cruft create /Users/hmalta01/projects/platform/templates/llm-service   # recommended: enables `cruft update`
uvx cookiecutter /Users/hmalta01/projects/platform/templates/llm-service   # plain, no updates
```

`cruft` records the template commit in `.cruft.json`, so `uvx cruft update` later pulls template fixes
into the generated project. It needs the template to be a git repo with the change committed.

## Options

| Option | Default | Meaning |
|---|---|---|
| `project_name` / `project_slug` / `package_name` | My LLM Service / my-llm-service / my_llm_service | Names |
| `app_type` | `fastapi` | `fastapi` or `azure-function` (HTTP trigger, v2 programming model) |
| `include_agent` | `n` | `y` adds a Microsoft Foundry prompt agent (`azure-ai-projects` 2.x) with a function tool and optional Azure AI Search grounding |
| `ai_utils_git` / `ai_utils_tag` | this repo's ai-utils, `v0.1.0` | Where the shared package comes from |
| `python_version` | `3.13` | |

## What you get

- `src/<package>/service.py`: core logic on `ai_utils.llm.LLMClient`, independent of the HTTP layer
- `api.py` (FastAPI) or `function_app.py` (Azure Function)
- `agent.py` (optional): deploy a Foundry agent version and ask it, handling function-call rounds
- `evals/run_eval.py`: runs `evals/data.jsonl` through the service (or agent) and scores it with
  `azure-ai-evaluation` built-ins plus an `ai_utils` `RubricJudge`
- `Dockerfile` + `.dockerignore` (`make docker-build` / `make docker-run`): multi-stage uv build, non-root user and
  healthcheck for FastAPI; the official Azure Functions base image for Functions. Built for linux/amd64 (Azure).
- `docs/AI_UTILS.md`: how to use every ai-utils tool (preprocessing, OCR, blob, RAG, eval, monitoring)
- ruff (120), mypy strict, pytest with SDKs mocked, pre-commit (ruff, mypy, gitleaks), GitHub Actions CI,
  `Makefile`, `CLAUDE.md`, `.env.example`
