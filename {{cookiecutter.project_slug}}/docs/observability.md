# Observability

The backend exports logs, traces and request telemetry to Application Insights through
`azure-monitor-opentelemetry` (`apps/backend/src/telemetry.py`). It is on when
`APPLICATIONINSIGHTS_CONNECTION_STRING` is set; without it the app only logs to stdout.
`infra/` sets the variable on the backend web app.

Every record carries `service.name`, `service.version` (`APP_VERSION`) and `deployment.environment`
(`ENVIRONMENT`), so dev, uat and prod are distinguishable even in a shared workspace.

## What is recorded

| Source | Table | Notes |
|---|---|---|
| Incoming HTTP calls | `requests` | Status, duration, success (FastAPI instrumentation) |
| Python logs | `traces` | Log `extra` fields become `customDimensions` |
| Unhandled errors | `exceptions` | |

### LLM log events

Emitted by `apps/backend/src/llm/client.py`, one per attempt:

| `message` | Level | When |
|---|---|---|
| `llm.completed` | INFO | The call succeeded and the answer passed validation |
| `llm.attempt_failed` | WARNING | One attempt failed (transport error, timeout, empty answer, invalid JSON) |
| `llm.retry` | WARNING | A retry is about to happen (`provider`, `attempt`) |
| `llm.provider_failed` | WARNING | A provider ran out of attempts; the next provider is tried |

`customDimensions` on `llm.completed` and `llm.attempt_failed`:

| Field | Meaning |
|---|---|
| `provider`, `model` | Who answered (`azure`, `ollama`) and the deployment/model name |
| `prompt`, `prompt_version` | Prompt file name and its `version` (see [prompt-versioning.md](prompt-versioning.md)) |
| `attempt` | Attempt number within the provider |
| `latency_ms` | Duration of that attempt only (not the backoff between attempts, not the whole request) |
| `input_tokens`, `output_tokens` | From the provider's usage; `null` when it reports none |
| `input`, `output` | The question and the raw LLM output, max 2000 chars. See below |
| `error_type`, `error` | Only on `llm.attempt_failed` |

### Logging the question and the answer

`LOG_LLM_CONTENT` controls `input` and `output`. Unset means on for `local` and `dev`, off for `uat` and `prod`.
They can contain personal data, so enable them in uat/prod only for a short, deliberate debugging window.

## Dashboard

`infra/workbook.tf` deploys an Azure Workbook (`infra/workbook.json`) on the Application Insights resource:
Application Insights, then Workbooks, then "<name> API". Panels:

- Requests and failures over time, success rate, requests by operation and status, latency p50/p95
- Tokens over time, tokens and latency by provider, model and prompt version
- Calls by provider (shows how often the fallback is used)
- Failed attempts by error, retries and provider failures
- Latest failed and successful calls (with input/output when logging them is on)
- Exceptions

The panels use the time range picker at the top. The workbook JSON was checked with `terraform validate` only:
open it once in the portal after the first deploy and adjust the queries there if needed.

## Useful queries

Run in Application Insights, then Logs.

```kusto
// Cost drivers: tokens per prompt version
traces
| where message == "llm.completed"
| summarize Calls=count(), In=sum(toint(customDimensions.input_tokens)), Out=sum(toint(customDimensions.output_tokens))
    by tostring(customDimensions.model), tostring(customDimensions.prompt_version)
```

```kusto
// Did a prompt change make things slower or worse?
traces
| where message in ("llm.completed", "llm.attempt_failed")
| summarize Calls=count(), Failed=countif(message == "llm.attempt_failed"),
    P95_ms=percentile(toint(customDimensions.latency_ms), 95)
    by tostring(customDimensions.prompt_version)
```

```kusto
// Follow one failing request: same operation_Id across requests, traces and exceptions
union requests, traces, exceptions
| where operation_Id == "<id from a failed request>"
| order by timestamp asc
```

## Local debugging

Without a connection string, the same events appear on stdout:

```bash
cd apps/backend && uv run uvicorn main:app --app-dir src --reload   # LOG_LEVEL=INFO shows llm.completed
```

## Limits

- Ingestion has a delay of a few minutes.
- Request/trace sampling is controlled by the distro (`OTEL_TRACES_SAMPLER*` settings; check the default of the installed
  version). Logs, which carry the LLM events, are not sampled. At high volume watch Log Analytics ingestion cost.
- Token counts depend on the provider reporting `usage`. Confirmed with Ollama; check Azure OpenAI after the first deploy.
