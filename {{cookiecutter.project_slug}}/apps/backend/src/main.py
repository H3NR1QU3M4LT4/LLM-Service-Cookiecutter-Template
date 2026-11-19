"""HTTP API."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes import llm, status
from security import require_api_key, security_headers
from telemetry import setup_telemetry

_settings = get_settings()
_PUBLIC_DOCS = _settings.environment == "local"

app = FastAPI(
    title="{{ cookiecutter.project_name }}",
    version=_settings.app_version,
    docs_url="/docs" if _PUBLIC_DOCS else None,
    redoc_url="/redoc" if _PUBLIC_DOCS else None,
    openapi_url="/openapi.json" if _PUBLIC_DOCS else None,
)
setup_telemetry(_settings, app)
app.middleware("http")(security_headers)
if _settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["X-API-Key", "Content-Type"],
    )
app.include_router(status.router)
app.include_router(llm.router, dependencies=[Depends(require_api_key)])
