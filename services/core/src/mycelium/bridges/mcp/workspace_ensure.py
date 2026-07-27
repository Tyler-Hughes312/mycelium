"""Ensure workspace is registered (and optionally indexed) for MCP tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mycelium.bridges.mcp.client import CoreHttp
from mycelium.bridges.mcp.formatters import resolve_workspace_id


def find_workspace_by_path(
    workspaces: list[dict[str, Any]], workspace_path: str
) -> dict[str, Any] | None:
    needle = workspace_path.rstrip("/")
    for w in workspaces:
        wp = str(w.get("path") or "").rstrip("/")
        if wp == needle or needle.startswith(wp + "/") or wp.endswith(needle):
            return w
    return None


def ensure_registered(
    core: CoreHttp,
    workspace_path: str,
) -> tuple[dict[str, Any], bool]:
    """Return (workspace, created). Registers a git repo if not already known.

    Does **not** start a full index (policy B).
    """
    path = str(Path(workspace_path).expanduser().resolve())
    rows = core.list_workspaces()
    existing = find_workspace_by_path(rows, path)
    if existing:
        return existing, False
    root = Path(path)
    if not root.is_dir():
        raise ValueError(f"workspace_path is not a directory: {path}")
    if not (root / ".git").exists():
        raise ValueError(
            f"workspace_path is not a git repo (missing .git): {path}. "
            "Init git or register via Mycelium Desktop Library."
        )
    ws = core.register_workspace(path)
    if not ws.get("id"):
        raise ValueError(f"register_workspace returned empty workspace for {path}")
    return ws, True


def maybe_start_index(
    core: CoreHttp,
    workspace_id: str,
    *,
    ensure_index: bool,
) -> dict[str, Any]:
    """Start full index when ensure_index and status is not complete/running."""
    status = core.index_status(workspace_id) or {}
    state = str(status.get("status") or "idle").lower()
    if not ensure_index:
        return {**status, "started": False, "skipped": True}
    if state in {"complete", "running", "indexing"}:
        return {**status, "started": False, "skipped": False}
    started = core.start_index(workspace_id)
    return {**(started or status), "started": True, "skipped": False}


def resolve_or_register(
    core: CoreHttp,
    workspace_id: str | None,
    workspace_path: str | None,
    *,
    default_all: bool = False,
    auto_register: bool = True,
) -> tuple[str, str | None]:
    """Resolve workspace id; optionally auto-register from path.

    Returns (workspace_id, hint) where hint is set when index looks empty.
    """
    rows = core.list_workspaces()
    hint: str | None = None
    try:
        wid = resolve_workspace_id(
            rows,
            workspace_id=workspace_id or None,
            workspace_path=workspace_path or None,
            default_all=default_all,
        )
    except ValueError:
        if not auto_register or not workspace_path:
            raise
        ws, _created = ensure_registered(core, workspace_path)
        wid = str(ws["id"])
        hint = (
            "Workspace was auto-registered but may be unindexed — "
            "call mycelium_session_start(workspace_path=..., ensure_index=True)."
        )
        return wid, hint

    if wid != "*" and workspace_path:
        # Already registered; still hint if idle/never indexed
        st = core.index_status(wid)
        state = str(st.get("status") or "idle").lower()
        if state in {"idle", "error", ""}:
            # Check workspace row symbols as weak signal
            row = next((w for w in rows if w.get("id") == wid), None) or {}
            if int(row.get("symbols") or 0) == 0 and state != "complete":
                hint = (
                    "Workspace may be unindexed — "
                    "call mycelium_session_start(workspace_path=..., ensure_index=True)."
                )
    return wid, hint
