"""Make the backend's modules (config, llm, models) importable; they are plain modules under apps/backend/src."""

import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[2] / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))
