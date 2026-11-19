# LLM Service Cookiecutter Template

A monorepo for one LLM service: a FastAPI backend (Semantic Kernel, Azure OpenAI / Foundry with an Ollama fallback,
retry, validated JSON, versioned prompts), a React + Vite + Tailwind frontend, Application Insights telemetry, and
Terragrunt infrastructure for `dev`, `uat` and `prod`. Use [llm-monorepo](../llm-monorepo) when you need several apps
(Functions, container jobs, APIM, Redis).

## Generate

```bash
uvx cruft create /Users/hmalta01/projects/platform/templates/llm-service   # recommended: enables `cruft update`
uvx cookiecutter /Users/hmalta01/projects/platform/templates/llm-service   # plain, no updates
```

`cruft` records the template commit in `.cruft.json`, so `uvx cruft update` later pulls template fixes into the
generated project. It needs the template to be a git repo with the change committed.

## Options

| Option | Default | Meaning |
|---|---|---|
| `project_name` / `project_slug` | My LLM Service / my-llm-service | Names; the slug prefixes every Azure resource |
| `project_description`, `author_name`, `author_email` | | Metadata; the email is the default budget alert recipient |
| `brand` | `lms` | `lms` (Leica Microsystems) or `lbs` (Leica Biosystems): logo in the navbar and name in the footer of both frontends |
| `python_version` | `3.13` | |
| `azure_location` | `westeurope` | Region for all resources |
| `azure_openai_model` | `gpt-5.6-luna` | Model deployed in Foundry (check regional availability) |
| `name_suffix` | `001` | Makes web app, registry and Foundry names globally unique |
| `budget_amount_dev` / `_uat` / `_prod` | 50 / 100 / 500 | Monthly budget per environment |
| `budget_alert_emails` | author email | Comma-separated; emailed at 80% of the budget |

## What you get

See the generated project's README. In short: `apps/backend`, `apps/frontend`, `infra/` (Terragrunt, `live/{dev,uat,prod}`),
`docs/` (observability, infrastructure, prompt versioning), `docker-compose.yml`, pre-commit hooks and GitHub Actions
(CI quality gates, infrastructure plan/apply/destroy per environment).

`apps/frontend/*`, `apps/backend/src/prompts/*` and `.github/*` are copied without rendering because they contain
`{{ }}` that Jinja would otherwise try to evaluate.
