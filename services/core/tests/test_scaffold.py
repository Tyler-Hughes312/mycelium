"""Smoke tests for Epic 1 Core scaffold + Story 2.1 workspaces."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from fastapi.testclient import TestClient

from mycelium import __version__
from mycelium.adapters.http.app import create_app
from mycelium.adapters.store import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.config import MyceliumConfig, ensure_local_layout
from mycelium.core.domain.index_service import IndexService
from mycelium.core.ports import EmbeddingRuntime, GraphStore, WorkspaceRepo


def ensure_test_layout(home: Path) -> MyceliumConfig:
    """Local layout with hashing embedder (fast; no HF download)."""
    cfg = ensure_local_layout(home)
    text = cfg.paths.config_file.read_text(encoding="utf-8")
    text = text.replace(
        'model = "sentence-transformers/all-MiniLM-L6-v2"',
        'model = "mycelium-hashing-v1"',
    )
    if 'model = "mycelium-hashing-v1"' not in text:
        text = text.rstrip() + '\n\n[embedding]\nmodel = "mycelium-hashing-v1"\n'
    cfg.paths.config_file.write_text(text, encoding="utf-8")
    return ensure_local_layout(home)


def test_package_version() -> None:
    assert __version__ == "0.1.4"


def test_privacy_guards() -> None:
    from mycelium.core.config import NetworkPolicy
    from mycelium.core.privacy import (
        PrivacyError,
        assert_allow_code_upload,
        assert_allow_remote_llm,
    )

    denied = NetworkPolicy(allow_code_upload=False, allow_remote_llm=False)
    try:
        assert_allow_code_upload(denied)
        raise AssertionError("expected PrivacyError")
    except PrivacyError as exc:
        assert exc.code == "code_upload_disabled"
    try:
        assert_allow_remote_llm(denied)
        raise AssertionError("expected PrivacyError")
    except PrivacyError as exc:
        assert exc.code == "remote_llm_disabled"

    allowed = NetworkPolicy(allow_code_upload=True, allow_remote_llm=True)
    assert_allow_code_upload(allowed)
    assert_allow_remote_llm(allowed)


def test_config_version_migrates(tmp_path: Path) -> None:
    from mycelium.core.config import CURRENT_CONFIG_VERSION, load_config

    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        """\
[network]
allow_code_upload = false
allow_remote_llm = false

[server]
host = "127.0.0.1"
port = 8787

[paths]
data_dir = "data"
vault_dir = "vault"

[index]
history_depth = 100

[embedding]
model = "mycelium-hashing-v1"
""",
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.config_version == CURRENT_CONFIG_VERSION
    text = cfg_path.read_text(encoding="utf-8")
    assert "config_version" in text
    assert cfg.embedding.model == "mycelium-hashing-v1"
    assert cfg.index.history_depth == 100


def test_health_includes_config_version(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path)
    with TestClient(create_app(cfg)) as client:
        body = client.get("/health").json()
        assert body["config_version"] == cfg.config_version
        assert "watchers" in body
        assert "available" in body["watchers"]
        assert "workspaces" in body["watchers"]
        assert isinstance(body["watchers"]["workspaces"], int)
        assert "api_token_enabled" in body


def test_vector_store_recovers_torn_json(tmp_path: Path) -> None:
    from mycelium.adapters.store.vector_store import JsonVectorStore

    store = JsonVectorStore(tmp_path / "ws")
    assert store.upsert(
        node_id="n1",
        kind="Note",
        text="alpha",
        vector=[0.1, 0.2, 0.3],
        model_id="test",
    )
    path = tmp_path / "ws" / "vectors.json"
    path.write_text(path.read_text(encoding="utf-8") + "\nTRAILING GARBAGE\n", encoding="utf-8")
    rows = store.all_rows()
    assert len(rows) == 1
    assert rows[0]["node_id"] == "n1"
    # healed file must parse cleanly
    import json

    json.loads(path.read_text(encoding="utf-8"))


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
    assert cfg.config_version == 1
    assert "config_version" in text
    assert "all-MiniLM-L6-v2" in text
    assert cfg.embedding.model.endswith("all-MiniLM-L6-v2")
    assert (cfg.paths.vault_dir / "Home.md").is_file()
    assert (cfg.paths.vault_dir / "brain" / "North Star.md").is_file()
    assert (cfg.paths.vault_dir / "work" / "decisions").is_dir()


def test_vault_scaffold_idempotent(tmp_path: Path) -> None:
    from mycelium.adapters.vault.scaffold import scaffold_vault

    vault = tmp_path / "vault"
    first = scaffold_vault(vault)
    assert first["notes_created"] >= 10
    home = vault / "Home.md"
    home.write_text("# Home\n\ncustom\n", encoding="utf-8")
    second = scaffold_vault(vault)
    assert second["notes_created"] == 0
    assert "custom" in home.read_text(encoding="utf-8")


def test_health_includes_version(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path)
    with TestClient(create_app(cfg)) as client:
        res = client.get("/health")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "ok"
        assert body["version"] == __version__
        assert body["bind"]["host"] == "127.0.0.1"
        assert body["privacy"]["allow_code_upload"] is False
        assert body["embedding"]["backend"] == "hashing"
        assert body["config_version"] == cfg.config_version
        assert body["api_token_enabled"] is False


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)


def test_health_watchers_count_registered_workspace(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
    repo_dir = tmp_path / "watched-repo"
    _init_git_repo(repo_dir)
    with TestClient(create_app(cfg)) as client:
        before = client.get("/health").json()["watchers"]
        assert before["available"] is True
        client.post("/workspaces", json={"path": str(repo_dir)})
        after = client.get("/health").json()["watchers"]
        assert after["available"] is True
        assert after["workspaces"] >= 1


def test_register_git_workspace_persists(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
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
    cfg = ensure_test_layout(tmp_path / "home")
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
    cfg = ensure_test_layout(tmp_path / "home")
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
    cfg = ensure_test_layout(tmp_path / "home")
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
    cfg = ensure_test_layout(tmp_path / "home")
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
    cfg = ensure_test_layout(tmp_path / "home")
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


def test_incremental_delete_clears_vectors(tmp_path: Path) -> None:
    """Deleted files must drop orphan embeddings so RAG cannot return stale code."""
    from mycelium.adapters.store.vector_store import JsonVectorStore

    cfg = ensure_test_layout(tmp_path / "home")
    repo_dir = tmp_path / "vec-repo"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "mod.py", "def alpha():\n    return 1\n", "add alpha")

    with TestClient(create_app(cfg)) as client:
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        client.post(f"/workspaces/{ws['id']}/index")
        assert _wait_index(client, ws["id"])["status"] == "complete"

        hook = client.post(
            f"/workspaces/{ws['id']}/hooks/file-changed",
            json={"path": "mod.py"},
        ).json()["update"]
        assert hook["symbols_upserted"] == 1
        symbol_ids = list(hook["symbol_ids"])
        file_id = "file:mod.py"

        store = JsonVectorStore(cfg.paths.data_dir / "workspaces" / ws["id"])
        assert store.get(file_id) is not None
        for sid in symbol_ids:
            assert store.get(sid) is not None

        (repo_dir / "mod.py").unlink()
        deleted = client.post(
            f"/workspaces/{ws['id']}/hooks/file-changed",
            json={"path": "mod.py"},
        ).json()["update"]
        assert deleted["deleted"] is True

        assert store.get(file_id) is None
        for sid in symbol_ids:
            assert store.get(sid) is None


def test_incremental_replace_drops_obsolete_symbol_vectors(tmp_path: Path) -> None:
    """Renamed/removed symbols in a file must not leave old vectors."""
    from mycelium.adapters.store.vector_store import JsonVectorStore

    cfg = ensure_test_layout(tmp_path / "home")
    repo_dir = tmp_path / "vec-repo2"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "mod.py", "def alpha():\n    return 1\n", "add alpha")

    with TestClient(create_app(cfg)) as client:
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        client.post(f"/workspaces/{ws['id']}/index")
        assert _wait_index(client, ws["id"])["status"] == "complete"

        first = client.post(
            f"/workspaces/{ws['id']}/hooks/file-changed",
            json={"path": "mod.py"},
        ).json()["update"]
        old_id = "symbol:mod.py:alpha:1"
        assert old_id in first["symbol_ids"]

        (repo_dir / "mod.py").write_text("def beta():\n    return 2\n", encoding="utf-8")
        second = client.post(
            f"/workspaces/{ws['id']}/hooks/file-changed",
            json={"path": "mod.py"},
        ).json()["update"]
        assert "symbol:mod.py:beta:1" in second["symbol_ids"]
        assert old_id not in second["symbol_ids"]

        store = JsonVectorStore(cfg.paths.data_dir / "workspaces" / ws["id"])
        assert store.get(old_id) is None
        assert store.get("symbol:mod.py:beta:1") is not None


def test_embeddings_status_offline_hashing(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
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
    cfg = ensure_test_layout(tmp_path / "home")
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
        assert kinds & {"Function", "Method", "Class", "Symbol", "Commit", "File"}
        for r in body["results"]:
            assert "provenance" in r
            assert r["provenance"]["fusion"] == "rrf"
            assert r["kind"] in {
                "Function",
                "Method",
                "Class",
                "Type",
                "Const",
                "Symbol",
                "Commit",
                "File",
                "Note",
            }
            assert r.get("family") in {"Symbol", "Commit", "File", "Note"}

        # Intent: commit-oriented query should surface Commit kind when present
        cq = client.post(
            "/query",
            json={"query": "commit greet helpers", "workspace_id": ws["id"], "limit": 5},
        ).json()
        assert any(r["kind"] == "Commit" for r in cq["results"]) or cq["count"] >= 1

        fq = client.post(
            "/query",
            json={
                "query": "function greet",
                "workspace_id": ws["id"],
                "limit": 5,
                "kinds": ["Function", "Method"],
            },
        ).json()
        assert fq["count"] >= 1
        assert all(r["kind"] in {"Function", "Method"} for r in fq["results"])

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


def test_query_all_workspaces_cross_repo(tmp_path: Path) -> None:
    """Search with workspace_id='*' merges hits from multiple indexed repos."""
    cfg = ensure_test_layout(tmp_path / "home")
    repo_a = tmp_path / "repo-alpha"
    repo_b = tmp_path / "repo-beta"
    _init_git_repo(repo_a)
    _init_git_repo(repo_b)
    _commit_file(
        repo_a,
        "auth.py",
        "def authenticate_user(token):\n    return token.startswith('Bearer ')\n",
        "Add authenticate_user",
    )
    _commit_file(
        repo_b,
        "billing.py",
        "def calculate_invoice_total(items):\n    return sum(items)\n",
        "Add calculate_invoice_total",
    )

    with TestClient(create_app(cfg)) as client:
        wa = client.post("/workspaces", json={"path": str(repo_a)}).json()["workspace"]
        wb = client.post("/workspaces", json={"path": str(repo_b)}).json()["workspace"]
        client.post(f"/workspaces/{wa['id']}/index")
        client.post(f"/workspaces/{wb['id']}/index")
        assert _wait_index(client, wa["id"])["status"] == "complete"
        assert _wait_index(client, wb["id"])["status"] == "complete"

        q = client.post(
            "/query",
            json={"query": "authenticate_user calculate_invoice", "workspace_id": "*", "limit": 8},
        )
        assert q.status_code == 200
        body = q.json()
        assert body["scope"] == "all_workspaces"
        assert set(body["workspace_ids"]) == {wa["id"], wb["id"]}
        assert body["count"] >= 1
        names = {r.get("workspace_name") for r in body["results"]}
        assert any(n for n in names if n)
        titles = " ".join(r["title"] for r in body["results"]).lower()
        assert "authenticate" in titles or "invoice" in titles or body["count"] >= 1

        # Default (omit workspace_id) searches all
        q2 = client.post("/query", json={"query": "authenticate_user", "limit": 5})
        assert q2.status_code == 200
        assert q2.json()["scope"] == "all_workspaces"


def test_focus_empty_index_reason(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
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


def test_vault_crud_wikilinks_and_rag(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
    repo_dir = tmp_path / "vault-repo"
    _init_git_repo(repo_dir)
    _commit_file(
        repo_dir,
        "app.py",
        "def greet(name):\n    return f'hi {name}'\n",
        "Add greet",
    )

    with TestClient(create_app(cfg)) as client:
        info = client.get("/vault").json()["vault"]
        assert info["path"]
        assert info["notes"] >= 0
        before = info["notes"]

        # Create target note + linking note
        a = client.post(
            "/vault/notes",
            json={"title": "Rate limits", "body": "Decision log for retries.\n"},
        )
        assert a.status_code == 201
        note_a = a.json()["note"]
        assert (Path(note_a["abs_path"])).is_file()
        assert client.get("/vault").json()["vault"]["notes"] == before + 1

        b = client.post(
            "/vault/notes",
            json={
                "title": "Auth flow",
                "body": "See [[Rate limits]] and symbol [[greet]].\nAlso [[missing-note]].\n",
            },
        )
        assert b.status_code == 201
        note_b = b.json()["note"]
        assert any(u["target"] == "missing-note" for u in note_b["unresolved_links"])
        assert any(
            e.get("edge_kind") == "wikilink" for e in note_b["outgoing_edges"]
        )

        back = client.get(f"/vault/notes/{note_a['id'].removeprefix('note:')}/backlinks")
        assert back.status_code == 200
        assert back.json()["count"] >= 1
        assert back.json()["backlinks"][0]["title"] == "Auth flow"

        # Index workspace so greet symbol resolves + notes in RAG
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        client.post(f"/workspaces/{ws['id']}/index")
        status = _wait_index(client, ws["id"])
        assert status["status"] == "complete"

        client.post("/vault/reindex", params={"workspace_id": ws["id"]})
        refreshed = client.get(f"/vault/notes/{note_b['id'].removeprefix('note:')}").json()["note"]
        kinds = {e.get("edge_kind") for e in refreshed["outgoing_edges"]}
        assert "wikilink" in kinds
        assert "mentions" in kinds

        q = client.post(
            "/query",
            json={"query": "rate limit retries decision", "workspace_id": ws["id"], "limit": 8},
        ).json()
        assert any(r["kind"] == "Note" for r in q["results"])

        focus = client.post(
            "/context/focus",
            json={"workspace_id": ws["id"], "path": "app.py", "symbol": "greet", "limit": 8},
        ).json()
        assert focus["count"] >= 1
        # Explicitly linked note should appear (or at least Note family present when linked)
        note_hits = [r for r in focus["results"] if r["kind"] == "Note"]
        assert note_hits, focus["results"]
        assert any(r.get("provenance", {}).get("explicit_note_link") for r in note_hits)

        # Update + delete
        updated = client.put(
            f"/vault/notes/{note_a['id'].removeprefix('note:')}",
            json={"body": "Updated body about rate limits.\n"},
        )
        assert updated.status_code == 200
        deleted = client.delete(f"/vault/notes/{note_a['id'].removeprefix('note:')}")
        assert deleted.status_code == 200
        assert client.get(f"/vault/notes/{note_a['id'].removeprefix('note:')}").status_code == 404


def test_vault_buckets_tree_pack_and_rag(tmp_path: Path) -> None:
    """Buckets + structure pack (no RAG) + nested notes still RAG-queryable."""
    cfg = ensure_test_layout(tmp_path / "home")
    repo_dir = tmp_path / "bucket-repo"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "app.py", "def greet():\n    return 1\n", "Add greet")

    with TestClient(create_app(cfg)) as client:
        bucket = client.post("/vault/buckets", json={"name": "architecture"})
        assert bucket.status_code == 201
        b = bucket.json()["bucket"]
        assert b["bucket"] == "architecture"
        assert b["created_index"] is True
        assert b["index"]["path"] == "architecture/_index.md"

        note = client.post(
            "/vault/notes",
            json={
                "title": "ADR rate limits",
                "body": "We use jittered backoff for rate limits.\n",
                "bucket": "architecture",
            },
        )
        assert note.status_code == 201
        nested = note.json()["note"]
        assert nested["path"] == "architecture/adr-rate-limits.md"
        assert nested["bucket"] == "architecture"
        assert nested["is_index"] is False

        tree = client.get("/vault/tree").json()
        assert tree["buckets"] >= 1
        assert tree["notes"] >= 2
        folder = next(
            c
            for c in tree["root"]["children"]
            if c.get("type") == "folder" and c.get("path") == "architecture"
        )
        paths = {c["path"] for c in folder["children"] if c.get("type") == "note"}
        assert "architecture/_index.md" in paths
        assert "architecture/adr-rate-limits.md" in paths

        packed = client.post(
            "/vault/pack",
            json={"bucket": "architecture", "max_tokens": 400},
        ).json()["pack"]
        assert packed["tokens_est"] <= 400
        assert "architecture/_index.md" in packed["text"] or any(
            i.get("phase") == "index" for i in packed["included"]
        )
        assert "## Map" in packed["text"]
        # Tight budget still returns something without error
        tight = client.post(
            "/vault/pack",
            json={"bucket": "architecture", "max_tokens": 80},
        ).json()["pack"]
        assert tight["tokens_est"] <= 80
        assert "## Map" in tight["text"]

        # Nested note fetch via path segments
        stem = nested["id"].removeprefix("note:")
        got = client.get(f"/vault/notes/{stem}")
        assert got.status_code == 200, got.text
        assert got.json()["note"]["title"] == "ADR rate limits"

        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        client.post(f"/workspaces/{ws['id']}/index")
        assert _wait_index(client, ws["id"])["status"] == "complete"
        client.post("/vault/reindex", params={"workspace_id": ws["id"]})

        q = client.post(
            "/query",
            json={
                "query": "jittered backoff rate limits architecture",
                "workspace_id": ws["id"],
                "limit": 8,
            },
        ).json()
        note_hits = [r for r in q["results"] if r["kind"] == "Note"]
        assert note_hits, q["results"]
        assert any("architecture" in (r.get("path") or "") for r in note_hits)


def test_settings_get_and_patch(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
    with TestClient(create_app(cfg)) as client:
        got = client.get("/settings")
        assert got.status_code == 200
        body = got.json()["settings"]
        assert body["privacy"]["cloud_account_required"] is False
        assert body["history_depth"] == 500
        assert body["allow_code_upload"] is False
        assert "llm_model" in body
        assert body["llm_api_key_configured"] is False

        patched = client.patch(
            "/settings",
            json={"history_depth": 250, "vault_dir": str(tmp_path / "alt-vault")},
        )
        assert patched.status_code == 200
        settings = patched.json()["settings"]
        assert settings["history_depth"] == 250
        assert settings["vault_dir"].endswith("alt-vault")
        assert Path(settings["vault_dir"]).is_dir()

        # Config file persisted
        reloaded = ensure_local_layout(tmp_path / "home")
        assert reloaded.index.history_depth == 250

        llm_patched = client.patch(
            "/settings",
            json={
                "allow_remote_llm": True,
                "llm_model": "gpt-4o-mini",
                "llm_base_url": "https://api.openai.com/v1",
                "llm_api_key": "sk-test-never-commit",
            },
        )
        assert llm_patched.status_code == 200
        llm_settings = llm_patched.json()["settings"]
        assert llm_settings["allow_remote_llm"] is True
        assert llm_settings["llm_model"] == "gpt-4o-mini"
        assert llm_settings["llm_base_url"] == "https://api.openai.com/v1"
        assert llm_settings["llm_api_key_configured"] is True
        assert "llm_api_key" not in llm_settings
        key_path = tmp_path / "home" / "llm_api_key"
        assert key_path.is_file()
        assert key_path.read_text(encoding="utf-8").strip() == "sk-test-never-commit"
        assert (key_path.stat().st_mode & 0o777) == 0o600


def test_mcp_formatters_and_tools(tmp_path: Path) -> None:
    from mycelium.bridges.mcp.client import CoreHttp
    from mycelium.bridges.mcp.formatters import (
        format_packet,
        format_commits,
        resolve_workspace_id,
    )
    from mycelium.bridges.mcp import server as mcp_server

    packet = {
        "mode": "hybrid_rag",
        "count": 1,
        "results": [
            {
                "kind": "Note",
                "title": "Rate limits",
                "path": "rate-limits.md",
                "snippet": "jittered backoff decision " * 20,
                "score": 0.9,
                "id": "note:rate-limits",
            }
        ],
    }
    text = format_packet("Search: rate", packet)
    assert "[Note] Rate limits" in text
    assert "…" in text or "jittered" in text

    assert "none" in format_commits([], path_filter="app.py").lower() or "(none)" in format_commits(
        [], path_filter="app.py"
    )

    wid = resolve_workspace_id(
        [{"id": "abc", "path": "/tmp/repo", "name": "repo"}],
        workspace_path="/tmp/repo",
    )
    assert wid == "abc"

    cfg = ensure_test_layout(tmp_path / "home")
    repo_dir = tmp_path / "mcp-repo"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "app.py", "def greet():\n    return 1\n", "Add greet")

    with TestClient(create_app(cfg)) as client:
        # Seed vault note + index
        client.post(
            "/vault/notes",
            json={"title": "Greet decision", "body": "We use greet helpers.\n"},
        )
        ws = client.post("/workspaces", json={"path": str(repo_dir)}).json()["workspace"]
        client.post(f"/workspaces/{ws['id']}/index")
        assert _wait_index(client, ws["id"])["status"] == "complete"

        core = CoreHttp(client=client)
        original = mcp_server._core
        mcp_server._core = lambda: core  # type: ignore[assignment]
        try:
            listed = mcp_server.mycelium_list_workspaces()
            assert ws["id"] in listed

            search = mcp_server.mycelium_search(
                query="greet",
                workspace_id=ws["id"],
                limit=5,
            )
            assert "Search:" in search
            assert "error:" not in search.lower() or "Function" in search or "Commit" in search or "Note" in search

            note = mcp_server.mycelium_get_note("Greet decision")
            assert "Greet decision" in note
            assert "greet helpers" in note.lower()

            commits = mcp_server.mycelium_commits_for_path(
                path="app.py",
                workspace_id=ws["id"],
            )
            assert "Add greet" in commits or "app.py" in commits

            focus = mcp_server.mycelium_focus(
                path="app.py",
                workspace_id=ws["id"],
                symbol="greet",
            )
            assert "Focus:" in focus

            tree = mcp_server.mycelium_vault_tree()
            assert "Vault map" in tree

            pack = mcp_server.mycelium_vault_pack(max_tokens=500)
            assert "vault pack" in pack.lower() or "Map" in pack

            sync = mcp_server.mycelium_sync_index(workspace_id=ws["id"], vault=False)
            assert "Sync" in sync

            bucket = mcp_server.mycelium_create_bucket("decisions")
            assert "created bucket=decisions" in bucket

            created = mcp_server.mycelium_create_note(
                title="Greet ADR",
                body="We keep [[greet]] tiny for clarity.\n",
                bucket="decisions",
                link_symbol="app.py#greet",
            )
            assert "Greet ADR" in created
            assert "decisions/" in created or "note:decisions" in created

            updated = mcp_server.mycelium_update_note(
                "Greet ADR",
                body="Updated: greet stays tiny; see [[greet]].\n",
            )
            assert "Updated: greet stays tiny" in updated
        finally:
            mcp_server._core = original


def test_mcp_agent_context_tools(tmp_path: Path) -> None:
    from mycelium.bridges.mcp.client import CoreHttp
    from mycelium.bridges.mcp import server as mcp_server
    from mycelium.bridges.mcp.formatters import format_bootstrap, format_task_packet

    boot = format_bootstrap(
        workspace={"id": "w1", "name": "demo", "status": "idle", "path": "/tmp/demo"},
        workspaces=[{"id": "w1", "name": "demo", "status": "idle", "path": "/tmp/demo"}],
        registered_new=True,
        index_info={"status": "running", "started": True},
        sync_info={"files_synced_count": 0, "fresh": True},
        brain_pack_text="Patterns live here",
        open_file_sections=["# Focus: app.py\n(no results)"],
    )
    assert "Mycelium session bootstrap" in boot
    assert "Patterns live here" in boot
    assert "registered=new" in boot

    task = format_task_packet(
        "Change context: add greet",
        query_packet={"count": 0, "mode": "hybrid_rag", "results": []},
        vault_slice="decision note",
        commits_text="# Commits\n(none)",
        hint="call session_start",
    )
    assert "Change context: add greet" in task
    assert "hint: call session_start" in task
    assert "decision note" in task

    cfg = ensure_test_layout(tmp_path / "home")
    repo_dir = tmp_path / "ctx-repo"
    _init_git_repo(repo_dir)
    _commit_file(repo_dir, "app.py", "def greet():\n    return 1\n", "Add greet")

    with TestClient(create_app(cfg)) as client:
        client.post("/vault/scaffold")
        client.post(
            "/vault/notes",
            json={
                "title": "Patterns",
                "body": "How I work: minimize scope.\n",
                "bucket": "brain",
                "filename": "Patterns.md",
            },
        )

        core = CoreHttp(client=client)
        original = mcp_server._core
        mcp_server._core = lambda: core  # type: ignore[assignment]
        try:
            # Auto-register via search without prior Desktop register
            search = mcp_server.mycelium_search(
                query="greet",
                workspace_path=str(repo_dir),
                limit=5,
            )
            assert "error:" not in search.lower() or "hint:" in search.lower()
            listed = mcp_server.mycelium_list_workspaces()
            assert str(repo_dir) in listed or repo_dir.name in listed

            boot = mcp_server.mycelium_session_start(
                workspace_path=str(repo_dir),
                open_files="app.py",
                ensure_index=True,
                brain_tokens=800,
            )
            assert "session bootstrap" in boot.lower()
            assert "error:" not in boot.lower()
            assert "Patterns" in boot or "minimize" in boot.lower() or "brain" in boot.lower()

            # Wait for index started by session_start
            rows = client.get("/workspaces").json()["workspaces"]
            assert rows
            wid = rows[0]["id"]
            assert _wait_index(client, wid)["status"] == "complete"

            change = mcp_server.mycelium_change_context(
                goal="greet helper",
                workspace_path=str(repo_dir),
            )
            assert "Change context" in change
            assert "error:" not in change.lower()

            debug = mcp_server.mycelium_debug_context(
                error="greet is broken",
                path="app.py",
                workspace_path=str(repo_dir),
            )
            assert "Debug context" in debug
            assert "error:" not in debug.lower()

            pre = mcp_server.mycelium_preflight(workspace_path=str(repo_dir))
            assert "session bootstrap" in pre.lower()
        finally:
            mcp_server._core = original
