"""Smoke tests for Epic 1 Core scaffold + Story 2.1 workspaces."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from fastapi.testclient import TestClient

from mycelium import __version__
from mycelium.adapters.http.app import create_app
from mycelium.adapters.store import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.config import ensure_local_layout
from mycelium.core.domain.index_service import IndexService
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
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
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


def _wait_index(client: TestClient, workspace_id: str, timeout: float = 10.0) -> dict:
    deadline = time.time() + timeout
    last: dict = {}
    while time.time() < deadline:
        last = client.get(f"/workspaces/{workspace_id}/index/status").json()["status"]
        if last.get("status") in {"complete", "failed", "cancelled"}:
            return last
        time.sleep(0.05)
    raise AssertionError(f"index did not finish: {last}")


def test_index_ingests_commit_nodes(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    repo_dir = tmp_path / "indexed-repo"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "readme.md", "hello\n", "Initial commit")
    _commit_file(
        repo_dir,
        "app.py",
        "def greet(name):\n    return f'hi {name}'\n\nclass Greeter:\n    pass\n",
        "Add app",
    )

    with TestClient(create_app(cfg)) as client:
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        started = client.post(f"/workspaces/{ws['id']}/index")
        assert started.status_code == 200
        assert started.json()["accepted"] is True
        status = _wait_index(client, ws["id"])
        assert status["status"] == "complete"
        assert status["commits_indexed"] == 2
        assert status["commits_total"] == 2
        assert status["symbols_indexed"] >= 1
        assert status["files_indexed"] >= 2
        assert status.get("edges_indexed", 0) >= 1

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

        symbols = client.get(f"/workspaces/{ws['id']}/symbols").json()["symbols"]
        names = {s["name"] for s in symbols}
        assert "greet" in names
        for s in symbols:
            assert s["kind"] == "Symbol"
            assert s["path"]
            assert s["start_line"] >= 1
            assert s["end_line"] >= s["start_line"]

        edges = client.get(f"/workspaces/{ws['id']}/edges").json()["edges"]
        assert any(e["edge_kind"] == "co_changed" for e in edges)
        assert any(
            {e["source_name"], e["target_name"]} == {"greet", "Greeter"} for e in edges
        )

        listed = client.get("/workspaces").json()["workspaces"][0]
        assert listed["commits"] == 2
        assert listed["symbols"] >= 1
        assert listed["status"] == "healthy"

        # Re-index is idempotent (AD-7)
        client.post(f"/workspaces/{ws['id']}/index")
        again = _wait_index(client, ws["id"])
        assert again["commits_total"] == 2
        assert again["symbols_indexed"] == status["symbols_indexed"]
        assert again["edges_indexed"] == status["edges_indexed"]


def test_unsupported_file_still_gets_file_node(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    repo_dir = tmp_path / "mixed-repo"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "notes.txt", "plain text\n", "Add notes")
    _commit_file(repo_dir, "util.py", "def helper():\n    return 1\n", "Add helper")

    with TestClient(create_app(cfg)) as client:
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        client.post(f"/workspaces/{ws['id']}/index")
        status = _wait_index(client, ws["id"])
        assert status["files_indexed"] >= 2
        symbols = client.get(f"/workspaces/{ws['id']}/symbols").json()["symbols"]
        assert any(s["name"] == "helper" for s in symbols)


def test_cancel_index_sets_cancelled_status(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    repo = JsonFileWorkspaceRepo(cfg.paths.data_dir)
    # Use sync service path with pre-set cancel to verify AD-7 cancel path
    svc = IndexService(
        data_dir=cfg.paths.data_dir,
        workspace_repo=repo,
        history_depth=500,
    )
    repo_dir = tmp_path / "cancel-repo"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "a.py", "def a():\n    return 1\n", "a")
    ws = repo.register(str(repo_dir))

    import threading

    cancel = threading.Event()
    cancel.set()
    with svc._lock:
        svc._cancel_events[ws["id"]] = cancel
        svc._running.add(ws["id"])
    try:
        from mycelium.core.domain.index_service import IndexCancelled

        try:
            svc._run_index(ws["id"], cancel.is_set, "t0")
            raise AssertionError("expected IndexCancelled")
        except IndexCancelled:
            pass
    finally:
        with svc._lock:
            svc._running.discard(ws["id"])
            svc._cancel_events.pop(ws["id"], None)


def test_incremental_file_hook_upserts_stable_symbol_ids(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    repo_dir = tmp_path / "inc-repo"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "mod.py", "def alpha():\n    return 1\n", "add alpha")

    with TestClient(create_app(cfg)) as client:
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        client.post(f"/workspaces/{ws['id']}/index")
        _wait_index(client, ws["id"])

        first = client.post(
            f"/workspaces/{ws['id']}/hooks/file-changed",
            json={"path": "mod.py"},
        )
        assert first.status_code == 200
        body = first.json()["update"]
        assert body["symbols_upserted"] == 1
        assert body["elapsed_ms"] < 500
        ids_1 = body["symbol_ids"]
        assert ids_1 == ["symbol:mod.py:alpha:1"]

        # Modify file (same symbol line → stable id)
        (repo_dir / "mod.py").write_text(
            "def alpha():\n    return 2\n\ndef beta():\n    return 3\n",
            encoding="utf-8",
        )
        second = client.post(
            f"/workspaces/{ws['id']}/hooks/file-changed",
            json={"path": str(repo_dir / "mod.py")},
        ).json()["update"]
        assert second["symbols_upserted"] == 2
        assert "symbol:mod.py:alpha:1" in second["symbol_ids"]
        assert "symbol:mod.py:beta:4" in second["symbol_ids"]
        assert second["elapsed_ms"] < 500

        symbols = client.get(f"/workspaces/{ws['id']}/symbols").json()["symbols"]
        names = {s["name"] for s in symbols if s["path"] == "mod.py"}
        assert names == {"alpha", "beta"}

        # Delete file → symbols removed
        (repo_dir / "mod.py").unlink()
        deleted = client.post(
            f"/workspaces/{ws['id']}/hooks/file-changed",
            json={"path": "mod.py"},
        ).json()["update"]
        assert deleted["deleted"] is True
        symbols_after = client.get(f"/workspaces/{ws['id']}/symbols").json()["symbols"]
        assert not any(s["path"] == "mod.py" for s in symbols_after)


def test_embeddings_status_offline_hashing(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    with TestClient(create_app(cfg)) as client:
        res = client.get("/embeddings/status")
        assert res.status_code == 200
        body = res.json()
        assert body["offline"] is True
        assert body["backend"] == "hashing"
        assert "notice" in body
        health = client.get("/health").json()
        assert health["embedding"]["backend"] == "hashing"


def test_hybrid_query_and_focus_after_index(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    repo_dir = tmp_path / "rag-repo"
    _init_git_repo(repo_dir)
    _commit_file(
        repo_dir,
        "app.py",
        "def greet(name):\n    return f'hi {name}'\n\ndef farewell(name):\n    return f'bye {name}'\n",
        "Add greet helpers",
    )

    with TestClient(create_app(cfg)) as client:
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        client.post(f"/workspaces/{ws['id']}/index")
        status = _wait_index(client, ws["id"])
        assert status["status"] == "complete"
        assert status.get("vectors_indexed", 0) >= 1

        empty = client.post(
            "/query",
            json={"query": "greet", "workspace_id": "missing", "limit": 5},
        )
        assert empty.status_code == 404

        q = client.post(
            "/query",
            json={"query": "greet helpers", "workspace_id": ws["id"], "limit": 5},
        )
        assert q.status_code == 200
        body = q.json()
        assert body["mode"] == "hybrid_rag"
        assert body["count"] <= 10
        assert body["count"] >= 1
        kinds = {r["kind"] for r in body["results"]}
        assert kinds & {"Symbol", "Commit"}
        for r in body["results"]:
            assert "provenance" in r
            assert r["provenance"]["fusion"] == "rrf"

        # Re-embed skips unchanged
        again = client.post(f"/workspaces/{ws['id']}/embeddings")
        assert again.status_code == 200
        emb = again.json()["embedding"]
        assert emb["skipped_unchanged"] >= 1

        focus = client.post(
            "/context/focus",
            json={
                "workspace_id": ws["id"],
                "path": "app.py",
                "symbol": "greet",
                "limit": 5,
            },
        )
        assert focus.status_code == 200
        pkt = focus.json()
        assert pkt["mode"] == "focus"
        assert pkt["count"] >= 1
        assert pkt["seed_id"]
        assert any(r.get("provenance", {}).get("seed") for r in pkt["results"])


def test_focus_empty_index_reason(tmp_path: Path) -> None:
    cfg = ensure_local_layout(tmp_path / "home")
    repo_dir = tmp_path / "empty-rag"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "readme.md", "x\n", "init")

    with TestClient(create_app(cfg)) as client:
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        focus = client.post(
            "/context/focus",
            json={"workspace_id": ws["id"], "path": "readme.md"},
        )
        assert focus.status_code == 200
        body = focus.json()
        assert body["count"] == 0
        assert body["reason"] == "empty_index"
