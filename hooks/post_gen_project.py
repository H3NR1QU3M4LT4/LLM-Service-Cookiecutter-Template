"""Drop the files of the app type and options not chosen, then initialise git."""

import subprocess
from pathlib import Path

PACKAGE = Path("src/{{ cookiecutter.package_name }}")
FASTAPI_FILES = [PACKAGE / "api.py", Path("tests/test_api.py")]
FUNCTION_FILES = [
    Path("function_app.py"),
    Path("host.json"),
    Path("local.settings.example.json"),
    Path("tests/test_function_app.py"),
]
AGENT_FILES = [PACKAGE / "agent.py", Path("tests/test_agent.py")]

remove = FUNCTION_FILES if "{{ cookiecutter.app_type }}" == "fastapi" else FASTAPI_FILES
if "{{ cookiecutter.include_agent }}" != "y":
    remove = [*remove, *AGENT_FILES]
for path in remove:
    path.unlink()

# macOS Finder litter copied from the template folder.
for junk in Path().rglob(".DS_Store"):
    junk.unlink()

subprocess.run(["git", "init", "--quiet"], check=False)
