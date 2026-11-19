"""Logging and Application Insights."""

import logging

from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

from config import Settings

SERVICE_NAME = "{{ cookiecutter.project_slug }}"


def setup_telemetry(settings: Settings, app: FastAPI) -> None:
    """Set the log level and, when a connection string is configured, export logs, traces and requests.

    Args:
        settings: Source of the log level, connection string, version and environment.
        app: The FastAPI app to instrument.
    """
    logging.basicConfig(level=settings.log_level)
    if not settings.applicationinsights_connection_string:
        return
    configure_azure_monitor(
        connection_string=settings.applicationinsights_connection_string,
        resource=Resource.create(
            {
                "service.name": SERVICE_NAME,
                "service.version": settings.app_version,
                "deployment.environment": settings.environment,
            }
        ),
    )
    FastAPIInstrumentor.instrument_app(app)
