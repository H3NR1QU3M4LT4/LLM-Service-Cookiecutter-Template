"""Clean build leftovers copied from the template, then create the Python lockfiles."""

import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Folders and files that only exist because someone ran the tools inside the template.
JUNK_DIRS = {"node_modules", "dist", ".terraform", ".terragrunt-cache", ".ruff_cache", ".mypy_cache", ".pytest_cache",
             ".venv", "__pycache__"}
JUNK_FILES = {".DS_Store"}
# Local env files that were sitting in the template folder (they can hold real keys); .env.example stays.

for path in sorted(Path(".").rglob("*"), key=lambda p: len(p.parts), reverse=True):
    if path.is_dir() and path.name in JUNK_DIRS:
        shutil.rmtree(path, ignore_errors=True)
    elif path.is_file() and (path.name in JUNK_FILES or (path.name.startswith(".env") and path.name != ".env.example")):
        path.unlink()

# Hooks are rendered by Jinja: never write doubled braces in them, and pass answers through `tojson`.
# Leica brand (cookiecutter `brand`): the default logo, footer name and Docker build argument of both frontends.
BRAND = {{ cookiecutter.brand | tojson }}
for target, old, new in [
    ("apps/frontend/src/layout/brand.ts", 'DEFAULT_BRAND: BrandKey = "lms"', f'DEFAULT_BRAND: BrandKey = "{BRAND}"'),
    ("apps/evals/dashboard/src/layout/brand.ts", 'DEFAULT_BRAND: BrandKey = "lms"', f'DEFAULT_BRAND: BrandKey = "{BRAND}"'),
    ("apps/frontend/Dockerfile", "ARG VITE_BRAND=lms", f"ARG VITE_BRAND={BRAND}"),
]:
    file = Path(target)
    file.write_text(file.read_text().replace(old, new))

# Browser tab titles and the navbar title: the project name (the dashboard adds "Evals").
NAME = {{ cookiecutter.project_name | tojson }}
for target, old, new in [
    ("apps/frontend/index.html", "<title>LLM Service</title>", f"<title>{html.escape(NAME)}</title>"),
    ("apps/frontend/src/App.tsx", 'title="LLM Service"', "title={" + json.dumps(NAME) + "}"),
    ("apps/evals/dashboard/index.html", "<title>LLM Evals</title>", f"<title>{html.escape(NAME + ' Evals')}</title>"),
    ("apps/evals/dashboard/src/App.tsx", 'title="LLM Evals"', "title={" + json.dumps(NAME + " Evals") + "}"),
]:
    file = Path(target)
    file.write_text(file.read_text().replace(old, new))

# uv.lock records the project name, so it cannot ship in the template.
uv = shutil.which("uv")
if uv is None:
    print("uv not found: run `uv lock` in apps/backend and apps/evals before building (CI and Docker need uv.lock).")
    sys.exit(0)

for app in ["apps/backend", "apps/evals"]:
    result = subprocess.run([uv, "lock"], cwd=Path(app), check=False)
    if result.returncode != 0:
        print(f"`uv lock` failed in {app}: fix the cause and run it again (CI and Docker need uv.lock).")
