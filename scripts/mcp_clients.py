#!/usr/bin/env python3
"""Merge Mycelium MCP into Cursor / VS Code / Codex / Windsurf / Claude Desktop configs.

Stdlib only. Used by scripts/install_mcp_clients.py.
"""

from __future__ import annotations

import json
import os
import platform
import re
from pathlib import Path
from typing import Any

DEFAULT_CORE_URL = "http://127.0.0.1:8787"

# Re-export Cursor helpers from the workspace-open module when imported side-by-side.
try:
    from cursor_workspace_open import (  # type: ignore
        DEFAULT_CORE_URL as _CWO_URL,
        install_user_hooks,
        install_user_mcp,
        merge_hooks_json,
        merge_mcp_json,
    )

    DEFAULT_CORE_URL = _CWO_URL
except ImportError:  # pragma: no cover — standalone copy
    install_user_hooks = None  # type: ignore[assignment]
    install_user_mcp = None  # type: ignore[assignment]
    merge_hooks_json = None  # type: ignore[assignment]
    merge_mcp_json = None  # type: ignore[assignment]


def mycelium_stdio_block(command: str, core_url: str = DEFAULT_CORE_URL) -> dict[str, Any]:
    return {
        "command": command,
        "args": [],
        "env": {"MYCELIUM_CORE_URL": core_url},
    }


def merge_mcp_servers_json(
    existing: dict[str, Any] | None,
    *,
    command: str,
    core_url: str = DEFAULT_CORE_URL,
    root_key: str = "mcpServers",
) -> dict[str, Any]:
    """Cursor / Windsurf / Claude Desktop shape: { mcpServers: { mycelium: … } }."""
    base: dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    servers = base.get(root_key)
    if not isinstance(servers, dict):
        servers = {}
    else:
        servers = dict(servers)
    servers["mycelium"] = mycelium_stdio_block(command, core_url)
    base[root_key] = servers
    return base


def merge_vscode_mcp_json(
    existing: dict[str, Any] | None,
    *,
    command: str,
    core_url: str = DEFAULT_CORE_URL,
) -> dict[str, Any]:
    """VS Code / Copilot shape: { servers: { mycelium: { type, command, … } } }."""
    base: dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    servers = base.get("servers")
    if not isinstance(servers, dict):
        servers = {}
    else:
        servers = dict(servers)
    servers["mycelium"] = {
        "type": "stdio",
        "command": command,
        "args": [],
        "env": {"MYCELIUM_CORE_URL": core_url},
    }
    base["servers"] = servers
    return base


_CODEX_MYCELIUM_BLOCK = """\
[mcp_servers.mycelium]
command = {command!r}
args = []
startup_timeout_sec = 30

[mcp_servers.mycelium.env]
MYCELIUM_CORE_URL = {core_url!r}
"""


def merge_codex_toml(
    existing: str,
    *,
    command: str,
    core_url: str = DEFAULT_CORE_URL,
) -> str:
    """Insert or replace [mcp_servers.mycelium] (+ .env) in Codex config.toml."""
    block = _CODEX_MYCELIUM_BLOCK.format(command=command, core_url=core_url).rstrip() + "\n"
    text = existing or ""
    # Drop any existing mycelium tables (header through next [section] or EOF)
    pattern = re.compile(
        r"(?ms)^\[mcp_servers\.mycelium(?:\.[^\]]+)?\][^\[]*"
    )
    text = pattern.sub("", text).rstrip() + ("\n\n" if text.strip() else "")
    return text + block


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def vscode_user_mcp_paths(home: Path) -> list[Path]:
    system = platform.system()
    paths: list[Path] = []
    if system == "Darwin":
        base = home / "Library" / "Application Support"
        for app in ("Code", "Code - Insiders", "Cursor"):
            # Cursor uses ~/.cursor/mcp.json; skip Cursor here
            if app == "Cursor":
                continue
            paths.append(base / app / "User" / "mcp.json")
    elif system == "Windows":
        appdata = Path(os.environ.get("APPDATA") or (home / "AppData" / "Roaming"))
        for app in ("Code", "Code - Insiders"):
            paths.append(appdata / app / "User" / "mcp.json")
    else:
        config = home / ".config"
        for app in ("Code", "Code - Insiders"):
            paths.append(config / app / "User" / "mcp.json")
    return paths


def windsurf_mcp_path(home: Path) -> Path:
    return home / ".codeium" / "windsurf" / "mcp_config.json"


def claude_desktop_config_path(home: Path) -> Path | None:
    system = platform.system()
    if system == "Darwin":
        return (
            home
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    if system == "Windows":
        appdata = Path(os.environ.get("APPDATA") or (home / "AppData" / "Roaming"))
        return appdata / "Claude" / "claude_desktop_config.json"
    # Linux — unofficial / varying; Claude Desktop is primarily macOS/Windows
    return home / ".config" / "Claude" / "claude_desktop_config.json"


def codex_config_path(home: Path) -> Path:
    return home / ".codex" / "config.toml"


def install_json_client(
    path: Path,
    *,
    command: str,
    core_url: str,
    kind: str,
) -> str:
    existing: dict[str, Any] | None = None
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    if kind == "vscode":
        merged = merge_vscode_mcp_json(existing, command=command, core_url=core_url)
    else:
        merged = merge_mcp_servers_json(existing, command=command, core_url=core_url)
    write_json(path, merged)
    return str(path)


def install_codex(
    path: Path,
    *,
    command: str,
    core_url: str,
) -> str:
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    merged = merge_codex_toml(existing, command=command, core_url=core_url)
    write_text(path, merged)
    return str(path)


def remove_mycelium_from_mcp_servers(path: Path) -> bool:
    """Remove mycelium from a Cursor-style mcp.json to avoid duplicates. Returns True if changed."""
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or "mycelium" not in servers:
        return False
    del servers["mycelium"]
    data["mcpServers"] = servers
    if not servers:
        # Leave empty mcpServers or delete file — keep file with other keys if any
        if set(data.keys()) <= {"mcpServers"}:
            path.unlink()
            return True
    write_json(path, data)
    return True
