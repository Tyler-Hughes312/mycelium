"""Tests for multi-client MCP config merges."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from mcp_clients import (  # noqa: E402
    merge_codex_toml,
    merge_mcp_servers_json,
    merge_vscode_mcp_json,
    remove_mycelium_from_mcp_servers,
)


def test_merge_vscode_uses_servers_key() -> None:
    merged = merge_vscode_mcp_json(
        {"servers": {"other": {"command": "x"}}},
        command="/bin/mycelium-mcp",
        core_url="http://127.0.0.1:8787",
    )
    assert "other" in merged["servers"]
    assert merged["servers"]["mycelium"]["type"] == "stdio"
    assert merged["servers"]["mycelium"]["command"] == "/bin/mycelium-mcp"


def test_merge_mcp_servers_preserves_others() -> None:
    merged = merge_mcp_servers_json(
        {"mcpServers": {"neon": {"command": "n"}}},
        command="/bin/mycelium-mcp",
    )
    assert "neon" in merged["mcpServers"]
    assert "mycelium" in merged["mcpServers"]


def test_merge_codex_toml_idempotent() -> None:
    first = merge_codex_toml("", command="/bin/mycelium-mcp", core_url="http://127.0.0.1:8787")
    assert "[mcp_servers.mycelium]" in first
    assert "command = '/bin/mycelium-mcp'" in first or 'command = "/bin/mycelium-mcp"' in first
    second = merge_codex_toml(first, command="/bin/mycelium-mcp-v2", core_url="http://127.0.0.1:8787")
    assert second.count("[mcp_servers.mycelium]\n") == 1
    assert "[mcp_servers.mycelium.env]" in second
    assert "mycelium-mcp-v2" in second


def test_merge_codex_preserves_unrelated() -> None:
    existing = 'model = "o3"\n\n[mcp_servers.other]\ncommand = "x"\n'
    out = merge_codex_toml(existing, command="/m", core_url="http://127.0.0.1:8787")
    assert 'model = "o3"' in out
    assert "[mcp_servers.other]" in out
    assert "[mcp_servers.mycelium]" in out


def test_remove_mycelium_from_project_mcp(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "mycelium": {"command": "a"},
                    "keep": {"command": "b"},
                }
            }
        ),
        encoding="utf-8",
    )
    assert remove_mycelium_from_mcp_servers(path) is True
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "mycelium" not in data["mcpServers"]
    assert "keep" in data["mcpServers"]
