"""Thin entrypoint — keeps `uvicorn main:app` working."""

from mycelium.adapters.http.app import DEFAULT_HOST, DEFAULT_PORT, app, create_app

__all__ = ["DEFAULT_HOST", "DEFAULT_PORT", "app", "create_app"]
