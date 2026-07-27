"""Tests for Cursor workspaceOpen auto-index helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from cursor_workspace_open import (  # noqa: E402
    ensure_and_maybe_index,
    install_user_hooks,
    install_user_mcp,
    is_git_repo,
    merge_hooks_json,
    merge_mcp_json,
    normalize_roots,
    process_workspace_open,
    should_start_index,
)


class FakeCore:
    def __init__(
        self,
        *,
        workspace_id: str = "ws-1",
        status: str = "idle",
    ) -> None:
        self.workspace_id = workspace_id
        self.status = status
        self.registered: list[str] = []
        self.started: list[str] = []

    def register_workspace(self, path: str) -> dict[str, Any]:
        self.registered.append(path)
        return {"id": self.workspace_id, "path": path}

    def index_status(self, workspace_id: str) -> dict[str, Any]:
        assert workspace_id == self.workspace_id
        return {"status": self.status, "workspace_id": workspace_id}

    def start_index(self, workspace_id: str) -> dict[str, Any]:
        self.started.append(workspace_id)
        self.status = "indexing"
        return {"status": "indexing", "workspace_id": workspace_id}


def test_should_start_index_skips_active_states() -> None:
    assert should_start_index({"status": "idle"}) is True
    assert should_start_index({"status": "error"}) is True
    assert should_start_index({}) is True
    assert should_start_index(None) is True
    assert should_start_index({"status": "complete"}) is False
    assert should_start_index({"status": "running"}) is False
    assert should_start_index({"status": "indexing"}) is False
    assert should_start_index({"status": "INDEXING"}) is False


def test_normalize_roots_prefers_payload_then_env() -> None:
    assert normalize_roots({"workspace_roots": ["/a", "/b"]}) == ["/a", "/b"]
    assert normalize_roots({}, env_project_dir="/c") == ["/c"]
    assert normalize_roots({}) == []


def test_is_git_repo(tmp_path: Path) -> None:
    bare = tmp_path / "bare"
    bare.mkdir()
    assert is_git_repo(bare) is False
    git = tmp_path / "repo"
    git.mkdir()
    (git / ".git").mkdir()
    assert is_git_repo(git) is True


def test_ensure_skips_non_git(tmp_path: Path) -> None:
    client = FakeCore()
    out = ensure_and_maybe_index(client, str(tmp_path / "nogit"))  # type: ignore[arg-type]
    assert out["skipped"] == "not_git_repo"
    assert client.registered == []
    assert client.started == []


def test_ensure_starts_when_idle(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    client = FakeCore(status="idle")
    out = ensure_and_maybe_index(client, str(repo))  # type: ignore[arg-type]
    assert out["started"] is True
    assert client.registered == [str(repo.resolve())]
    assert client.started == ["ws-1"]


def test_ensure_skips_when_complete(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    client = FakeCore(status="complete")
    out = ensure_and_maybe_index(client, str(repo))  # type: ignore[arg-type]
    assert out["started"] is False
    assert client.started == []


def test_process_fail_open_on_client_error(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    class Boom:
        def register_workspace(self, path: str) -> dict[str, Any]:
            raise OSError("core down")

    results = process_workspace_open(
        {"workspace_roots": [str(repo)]},
        core_url="http://127.0.0.1:9",
        client=Boom(),  # type: ignore[arg-type]
    )
    assert results[0]["skipped"] == "core_unreachable"
    assert results[0]["started"] is False


def test_merge_hooks_preserves_unrelated() -> None:
    existing = {
        "version": 1,
        "hooks": {
            "sessionStart": [{"command": "./keep-me.sh"}],
            "workspaceOpen": [{"command": "./other-open.sh"}],
        },
    }
    merged = merge_hooks_json(
        existing,
        command="/Users/me/.mycelium/bin/cursor-workspace-open",
    )
    assert merged["hooks"]["sessionStart"] == [{"command": "./keep-me.sh"}]
    cmds = [e["command"] for e in merged["hooks"]["workspaceOpen"]]
    assert "./other-open.sh" in cmds
    assert any("cursor-workspace-open" in c for c in cmds)


def test_merge_hooks_idempotent() -> None:
    first = merge_hooks_json(
        None,
        command="/home/u/.mycelium/bin/cursor-workspace-open",
    )
    second = merge_hooks_json(
        first,
        command="/home/u/.mycelium/bin/cursor-workspace-open",
    )
    assert len(second["hooks"]["workspaceOpen"]) == 1


def test_merge_mcp_preserves_other_servers() -> None:
    existing = {
        "mcpServers": {
            "github": {"command": "gh-mcp"},
        }
    }
    merged = merge_mcp_json(
        existing,
        mycelium_mcp_command="/repo/venv/bin/mycelium-mcp",
        core_url="http://127.0.0.1:8787",
    )
    assert "github" in merged["mcpServers"]
    assert merged["mcpServers"]["mycelium"]["command"] == "/repo/venv/bin/mycelium-mcp"
    assert (
        merged["mcpServers"]["mycelium"]["env"]["MYCELIUM_CORE_URL"]
        == "http://127.0.0.1:8787"
    )


def test_install_user_hooks_and_mcp(tmp_path: Path) -> None:
    home = tmp_path / "home"
    script = home / ".mycelium" / "bin" / "cursor-workspace-open"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env python3\nprint('{}')\n", encoding="utf-8")

    hooks = home / ".cursor" / "hooks.json"
    hooks.parent.mkdir(parents=True)
    hooks.write_text(
        json.dumps(
            {
                "version": 1,
                "hooks": {"beforeShellExecution": [{"command": "./audit.sh"}]},
            }
        ),
        encoding="utf-8",
    )

    install_user_hooks(hooks_path=hooks, script_path=script)
    data = json.loads(hooks.read_text(encoding="utf-8"))
    assert "beforeShellExecution" in data["hooks"]
    assert any(
        "cursor-workspace-open" in e.get("command", "")
        for e in data["hooks"]["workspaceOpen"]
    )

    mcp = home / ".cursor" / "mcp.json"
    install_user_mcp(
        mcp_path=mcp,
        mycelium_mcp_command=str(tmp_path / "venv" / "bin" / "mycelium-mcp"),
    )
    mcp_data = json.loads(mcp.read_text(encoding="utf-8"))
    assert "mycelium" in mcp_data["mcpServers"]
