# pylint: disable=wrong-import-position
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import Settings

# Hermetic tests: a developer's own apps/backend/.env (API_KEY, ENVIRONMENT...) or shell variables must not change them.
Settings.model_config["env_file"] = None
for _field in Settings.model_fields:  # pylint: disable=not-an-iterable
    os.environ.pop(_field.upper(), None)
