"""Smoke tests for Epic 1 Core scaffold + Story 2.1 workspaces."""

from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from mycelium import __version__
from mycelium.adapters.http.app import create_app
from mycelium.adapters.store import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.config import ensure_local_layout
from mycelium.core.ports import EmbeddingRuntime, GraphStore, WorkspaceRepo


def test_package_version() -> None:
    assert __version__ == "0.0.1"


def test_ports_are_protocols() -> None:
    assert GraphStore is not None
    assert EmbeddingRuntime is not None
    assert WorkspaceRepo is not None


def test_ensure_local_layout(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path)
    assert cfg.paths.config_file.exists()
    assert cfg.paths.data_dir.is_dir()
    assert cfg.paths.vault_dir.is_dir()
    text = cfg.paths.config_file.read_text(encoding="utf-8")
    assert "allow_code_upload = false" in text
    assert cfg.network.allow_code_upload is False
    assert cfg.server.host == "127.0.0.1"
    assert cfg.index.history_depth == 500


def test_health_includes_version(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path)
    with TestClient(create_app(cfg)) as client:
        res = client.get("/health")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "ok"
        assert body["version"] == __version__
        assert body["bind"]["host"] == "127.0.0.1"
        assert body["privacy"]["allow_code_upload"] is False


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)


def test_register_git_workspace_persists(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    repo_dir = tmp_path / "my-repo"
    _init_git_repo(repo_dir)

    with TestClient(create_app(cfg)) as client:
        created = client.post("/workspaces", json={"path": str(repo_dir)})
        assert created.status_code == 201
        ws = created.json()["workspace"]
        assert ws["path"] == str(repo_dir.resolve())
        assert ws["status"] == "idle"
        assert "id" in ws

        listed = client.get("/workspaces")
        assert listed.status_code == 200
        rows = listed.json()["workspaces"]
        assert len(rows) == 1
        assert rows[0]["id"] == ws["id"]

        # Idempotent re-register
        again = client.post("/workspaces", json={"path": str(repo_dir)})
        assert again.status_code == 201
        assert again.json()["workspace"]["id"] == ws["id"]
        assert len(client.get("/workspaces").json()["workspaces"]) == 1


def test_register_non_git_returns_structured_error(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    plain = tmp_path / "not-git"
    plain.mkdir()

    with TestClient(create_app(cfg)) as client:
        res = client.post("/workspaces", json={"path": str(plain)})
        assert res.status_code == 400
        detail = res.json()["detail"]
        assert detail["code"] == "not_git_repo"
        assert "git" in detail["message"].lower()


def test_json_repo_rejects_missing_path(tmp_path: Path) -> None:
    repo = JsonFileWorkspaceRepo(tmp_path)
    try:
        repo.register(str(tmp_path / "missing"))
        raise AssertionError("expected WorkspaceError")
    except WorkspaceError as exc:
        assert exc.code == "not_found"


def _commit_file(repo: Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", name], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@mycelium.local",
            "-c",
            "user.name=Mycelium Test",
            "commit",
            "-m",
            message,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def test_index_ingests_commit_nodes(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    repo_dir = tmp_path / "indexed-repo"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "readme.md", "hello\n", "Initial commit")
    _commit_file(repo_dir, "app.py", "print('hi')\n", "Add app")

    with TestClient(create_app(cfg)) as client:
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        indexed = client.post(f"/workspaces/{ws['id']}/index")
        assert indexed.status_code == 200
        body = indexed.json()["index"]
        assert body["status"] == "complete"
        assert body["commits_indexed"] == 2
        assert body["commits_total"] == 2

        commits = client.get(f"/workspaces/{ws['id']}/commits").json()["commits"]
        assert len(commits) == 2
        assert {c["message"] for c in commits} == {"Initial commit", "Add app"}
        for c in commits:
            assert c["kind"] == "Commit"
            assert c["hash"]
            assert c["author"]
            assert c["timestamp"]
            assert isinstance(c["changed_paths"], list)
            assert c["changed_paths"]

        status = client.get(f"/workspaces/{ws['id']}/index/status").json()["status"]
        assert status["status"] == "complete"
        assert status["progress"] == 100

        listed = client.get("/workspaces").json()["workspaces"][0]
        assert listed["commits"] == 2
        assert listed["status"] == "healthy"

        # Re-index is idempotent (AD-7)
        again = client.post(f"/workspaces/{ws['id']}/index").json()["index"]
        assert again["commits_total"] == 2
