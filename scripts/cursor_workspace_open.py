#!/usr/bin/env python3
"""Cursor workspaceOpen hook — register git roots with Mycelium Core and start index.

Stdlib only so ~/.mycelium/bin/cursor-workspace-open works without the repo venv.
Fail-open: never block Cursor (always exit 0, print {}).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CORE_URL = "http://127.0.0.1:8787"
CONNECT_TIMEOUT_S = 2.0
INDEX_SKIP_STATES = frozenset({"complete", "running", "indexing"})
HOOK_COMMAND_MARKER = "cursor-workspace-open"


def is_git_repo(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def should_start_index(status: dict[str, Any] | None) -> bool:
    """True when Core should begin a full index for this workspace."""
    state = str((status or {}).get("status") or "idle").lower()
    return state not in INDEX_SKIP_STATES


def normalize_roots(
    payload: dict[str, Any],
    *,
    env_project_dir: str | None = None,
) -> list[str]:
    roots = payload.get("workspace_roots")
    if isinstance(roots, list) and roots:
        return [str(r).strip() for r in roots if str(r).strip()]
    fallback = (env_project_dir or "").strip()
    return [fallback] if fallback else []


def _http_json(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    *,
    timeout: float = CONNECT_TIMEOUT_S,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        if not raw.strip():
            return {}
        return json.loads(raw)


class CoreClient:
    """Minimal Core HTTP client (stdlib urllib)."""

    def __init__(self, base_url: str, *, timeout: float = CONNECT_TIMEOUT_S) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def register_workspace(self, path: str) -> dict[str, Any]:
        out = _http_json(
            "POST",
            f"{self.base_url}/workspaces",
            {"path": path},
            timeout=self.timeout,
        )
        return dict(out.get("workspace") or {})

    def index_status(self, workspace_id: str) -> dict[str, Any]:
        out = _http_json(
            "GET",
            f"{self.base_url}/workspaces/{workspace_id}/index/status",
            timeout=self.timeout,
        )
        return dict(out.get("status") or {})

    def start_index(self, workspace_id: str) -> dict[str, Any]:
        out = _http_json(
            "POST",
            f"{self.base_url}/workspaces/{workspace_id}/index",
            {},
            timeout=self.timeout,
        )
        return dict(out.get("status") or {})


def ensure_and_maybe_index(
    client: CoreClient,
    workspace_path: str,
) -> dict[str, Any]:
    """Register a git repo and start index if idle. Raises on hard HTTP failures."""
    root = Path(workspace_path).expanduser().resolve()
    if not is_git_repo(root):
        return {"path": str(root), "skipped": "not_git_repo", "started": False}

    ws = client.register_workspace(str(root))
    wid = str(ws.get("id") or "")
    if not wid:
        return {"path": str(root), "skipped": "no_workspace_id", "started": False}

    status = client.index_status(wid)
    if not should_start_index(status):
        return {
            "path": str(root),
            "workspace_id": wid,
            "started": False,
            "index_status": status.get("status"),
        }

    started = client.start_index(wid)
    return {
        "path": str(root),
        "workspace_id": wid,
        "started": True,
        "index_status": started.get("status") or status.get("status"),
    }


def process_workspace_open(
    payload: dict[str, Any],
    *,
    core_url: str,
    env_project_dir: str | None = None,
    client: CoreClient | None = None,
) -> list[dict[str, Any]]:
    roots = normalize_roots(payload, env_project_dir=env_project_dir)
    if not roots:
        return []

    http = client or CoreClient(core_url)
    results: list[dict[str, Any]] = []
    for root in roots:
        try:
            results.append(ensure_and_maybe_index(http, root))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
            results.append({"path": root, "skipped": "core_unreachable", "started": False})
        except Exception:  # noqa: BLE001 — fail-open for Cursor
            results.append({"path": root, "skipped": "error", "started": False})
    return results


def merge_hooks_json(
    existing: dict[str, Any] | None,
    *,
    command: str,
    timeout: int = 10,
) -> dict[str, Any]:
    """Merge workspaceOpen hook without wiping unrelated hooks."""
    base: dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    base.setdefault("version", 1)
    hooks = base.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
    else:
        hooks = dict(hooks)

    entries = hooks.get("workspaceOpen")
    if not isinstance(entries, list):
        entries = []
    else:
        entries = list(entries)

    already = False
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        cmd = str(entry.get("command") or "")
        if HOOK_COMMAND_MARKER in cmd:
            already = True
            break
    if not already:
        entries.append({"command": command, "timeout": timeout})

    hooks["workspaceOpen"] = entries
    base["hooks"] = hooks
    return base


def merge_mcp_json(
    existing: dict[str, Any] | None,
    *,
    mycelium_mcp_command: str,
    core_url: str = DEFAULT_CORE_URL,
) -> dict[str, Any]:
    """Merge mycelium MCP server into user mcp.json without wiping others."""
    base: dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    servers = base.get("mcpServers")
    if not isinstance(servers, dict):
        servers = {}
    else:
        servers = dict(servers)

    servers["mycelium"] = {
        "command": mycelium_mcp_command,
        "args": [],
        "env": {"MYCELIUM_CORE_URL": core_url},
    }
    base["mcpServers"] = servers
    return base


def install_user_hooks(
    *,
    hooks_path: Path,
    script_path: Path,
    timeout: int = 10,
) -> dict[str, Any]:
    existing: dict[str, Any] | None = None
    if hooks_path.is_file():
        existing = json.loads(hooks_path.read_text(encoding="utf-8"))
    merged = merge_hooks_json(
        existing,
        command=str(script_path),
        timeout=timeout,
    )
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    hooks_path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return merged


def install_user_mcp(
    *,
    mcp_path: Path,
    mycelium_mcp_command: str,
    core_url: str = DEFAULT_CORE_URL,
) -> dict[str, Any]:
    existing: dict[str, Any] | None = None
    if mcp_path.is_file():
        existing = json.loads(mcp_path.read_text(encoding="utf-8"))
    merged = merge_mcp_json(
        existing,
        mycelium_mcp_command=mycelium_mcp_command,
        core_url=core_url,
    )
    mcp_path.parent.mkdir(parents=True, exist_ok=True)
    mcp_path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return merged


def main(argv: list[str] | None = None) -> int:
    _ = argv  # Cursor passes nothing; payload is stdin JSON
    core_url = os.environ.get("MYCELIUM_CORE_URL", DEFAULT_CORE_URL).strip() or DEFAULT_CORE_URL
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    payload: dict[str, Any] = {}
    if raw.strip():
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                payload = loaded
        except json.JSONDecodeError:
            payload = {}

    process_workspace_open(
        payload,
        core_url=core_url,
        env_project_dir=os.environ.get("CURSOR_PROJECT_DIR"),
    )
    # Cursor workspaceOpen expects optional pluginPaths; empty object is fine.
    sys.stdout.write("{}\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # noqa: BLE001 — never break Cursor open
        try:
            sys.stdout.write("{}\n")
        except Exception:  # noqa: BLE001
            pass
        raise SystemExit(0)
