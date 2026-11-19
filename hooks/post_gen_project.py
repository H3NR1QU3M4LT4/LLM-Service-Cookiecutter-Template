"""Clean build leftovers copied from the template, then create the Python lockfiles."""

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

# uv.lock records the project name, so it cannot ship in the template.
uv = shutil.which("uv")
if uv is None:
    print("uv not found: run `uv lock` in apps/backend and apps/evals before building (CI and Docker need uv.lock).")
    sys.exit(0)

for app in ["apps/backend", "apps/evals"]:
    result = subprocess.run([uv, "lock"], cwd=Path(app), check=False)
    if result.returncode != 0:
        print(f"`uv lock` failed in {app}: fix the cause and run it again (CI and Docker need uv.lock).")
