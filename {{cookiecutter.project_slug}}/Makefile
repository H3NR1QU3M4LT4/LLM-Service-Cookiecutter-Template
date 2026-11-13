.PHONY: sync test lint format type-check check eval run docker-build docker-run{% if cookiecutter.app_type == "azure-function" %} requirements{% endif %}{% if cookiecutter.include_agent == "y" %} agent-deploy{% endif %}

sync:
	uv sync
	uv run pre-commit install --hook-type pre-commit --hook-type pre-push

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run pylint --score=n src evals{% if cookiecutter.app_type == "azure-function" %} function_app.py{% endif %}

format:
	uv run ruff format .

type-check:
	uv run mypy

check: lint type-check test

eval:
	uv run python -m evals.run_eval
{% if cookiecutter.app_type == "fastapi" %}
run:
	uv run uvicorn {{ cookiecutter.package_name }}.api:app --reload
{%- else %}
run: requirements
	func start

# Azure Functions installs from requirements.txt, not uv.lock.
requirements:
	uv export --no-dev --no-hashes --no-emit-project --output-file requirements.txt
	echo "." >> requirements.txt
{%- endif %}
{%- if cookiecutter.include_agent == "y" %}

agent-deploy:
	uv run python -m {{ cookiecutter.package_name }}.agent deploy
{%- endif %}

IMAGE ?= {{ cookiecutter.project_slug }}
# Azure runs linux/amd64; images built on Apple Silicon default to arm64 and would not start there.
PLATFORM ?= linux/amd64

docker-build:
	docker build --platform $(PLATFORM) -t $(IMAGE) .

docker-run:
{%- if cookiecutter.app_type == "fastapi" %}
	docker run --rm --platform $(PLATFORM) -p 8000:8000 --env-file .env $(IMAGE)
{%- else %}
	docker run --rm --platform $(PLATFORM) -p 8080:80 --env-file .env $(IMAGE)
{%- endif %}
