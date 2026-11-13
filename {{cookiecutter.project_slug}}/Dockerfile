# syntax=docker/dockerfile:1
{%- if cookiecutter.app_type == "fastapi" %}
# Build: make docker-build   Run: make docker-run   (reads .env, serves http://localhost:8000)

FROM ghcr.io/astral-sh/uv:python{{ cookiecutter.python_version }}-bookworm-slim AS build
# git: ai-utils is installed from its git tag.
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
# Dependencies first, so code changes don't invalidate this layer.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

FROM python:{{ cookiecutter.python_version }}-slim-bookworm
RUN useradd --create-home --uid 1000 app
COPY --from=build --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
WORKDIR /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)"]
CMD ["uvicorn", "{{ cookiecutter.package_name }}.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
{%- else %}
# Build: make docker-build   Run: make docker-run   (reads .env, serves http://localhost:8080/api/ask)
# Same image runs on Azure Functions (Premium / Container Apps) or any container host.
# linux/amd64 on both stages: the Functions base image has no arm64 build, and the installed wheels must match it.

FROM --platform=linux/amd64 ghcr.io/astral-sh/uv:python{{ cookiecutter.python_version }}-bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt
COPY README.md ./
COPY src ./src
# Install into a plain folder the Functions host puts on sys.path (its own Python, not a venv).
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --target /packages -r requirements.txt . --python /usr/local/bin/python

FROM --platform=linux/amd64 mcr.microsoft.com/azure-functions/python:4-python{{ cookiecutter.python_version }}
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
    PYTHONPATH=/home/site/wwwroot/.python_packages
COPY --from=build /packages /home/site/wwwroot/.python_packages
COPY host.json function_app.py /home/site/wwwroot/
{%- endif %}
