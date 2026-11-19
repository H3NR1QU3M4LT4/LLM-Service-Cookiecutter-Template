# Prompt versioning

Prompts are code: files in git, reviewed in pull requests, released with the app.

- Prompts live in `apps/backend/src/prompts/<name>.yaml`, loaded by `src/llm/prompts.py` into a Semantic Kernel
  `PromptTemplateConfig`.
- Each file has a `version` (semver: patch = wording, minor = behaviour, major = output contract).
- `apps/backend/tests/test_prompts.py` pins the SHA-256 of every template. Edit a template without bumping the
  version and the test fails, printing the new `(version, hash)` to paste into `PINNED`.
- The prompt name and version are logged on every LLM call (`prompt`, `prompt_version`) and the loaded versions
  appear on `GET /status` under `prompts`, so any answer can be traced to the exact prompt.
- The release version is `APP_VERSION` (set from the git tag by CI/deploy).

## Add or change a prompt

1. Edit or add `src/prompts/<name>.yaml`; bump `version`.
2. Update `PINNED` in `tests/test_prompts.py`.
3. Compare behaviour by `prompt_version` in the dashboard after release (see [observability.md](observability.md)).

User input is always passed as a template variable (HTML-encoded by the template engine), never concatenated into
the template, and wrapped in `<user_input>` so it cannot close the tag or open extra messages.
