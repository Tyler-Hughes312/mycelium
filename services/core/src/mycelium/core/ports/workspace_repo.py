"""Workspace repository port — registered git repos."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class WorkspaceRepo(Protocol):
    """Register and list local workspace repos (FR-2)."""

    def list_workspaces(self) -> list[dict[str, Any]]:
        """Return all registered workspaces."""
        ...

    def register(self, path: str) -> dict[str, Any]:
        """Register a local git path; raise on invalid path."""
        ...

    def get(self, workspace_id: str) -> dict[str, Any] | None:
        """Fetch one workspace by id."""
        ...
