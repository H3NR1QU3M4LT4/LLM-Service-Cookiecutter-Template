# syntax=docker/dockerfile:1
# Build: docker build --build-arg APP_VERSION=1.0.0 -t {{ cookiecutter.project_slug }} .
# Run:   docker run --env-file .env -e ENVIRONMENT=dev -p 8000:8000 {{ cookiecutter.project_slug }}
FROM ghcr.io/astral-sh/uv:python{{ cookiecutter.python_version }}-bookworm-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project --no-editable

FROM python:{{ cookiecutter.python_version }}-slim-bookworm
RUN useradd --create-home --uid 1000 app
COPY --from=build --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app src /app/src
ARG APP_VERSION=0.0.1
# Fail closed: the image defaults to prod (API_KEY required, /docs off); override per deployment.
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 APP_VERSION=$APP_VERSION ENVIRONMENT=prod
WORKDIR /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/status', timeout=4)"]
CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
