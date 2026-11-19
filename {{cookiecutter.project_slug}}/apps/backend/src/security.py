"""API key auth and response security headers."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import APIKeyHeader

from config import Settings, get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    key: Annotated[str | None, Depends(_api_key_header)], settings: Annotated[Settings, Depends(get_settings)]
) -> None:
    """Reject requests without the configured API key. No key configured is accepted only locally."""
    if not settings.api_key:
        if settings.environment == "local":
            return
        raise HTTPException(status_code=503, detail="API key not configured.")
    if key is None or not secrets.compare_digest(key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key.")


async def security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201
    """Add baseline security headers to every response."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    return response
