"""HTTP /threads API — TestClient + Echo LLM (no real API keys)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from mycelium.adapters.http.app import create_app
from mycelium.adapters.llm.echo import EchoLlm
from mycelium.core.config import MyceliumConfig, ensure_local_layout


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


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)


def _register_workspace(client: TestClient, tmp_path: Path) -> str:
    repo_dir = tmp_path / "chat-repo"
    _init_git_repo(repo_dir)
    res = client.post("/workspaces", json={"path": str(repo_dir)})
    assert res.status_code == 201, res.text
    return str(res.json()["workspace"]["id"])


def test_messages_endpoint_returns_receipt(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
    app = create_app(cfg)
    with TestClient(app) as client:
        app.state.chat_llm = EchoLlm()
        ws_id = _register_workspace(client, tmp_path)

        created = client.post("/threads", json={"workspace_id": ws_id, "title": "demo"})
        assert created.status_code == 201, created.text
        thread = created.json()["thread"]
        thread_id = thread["id"]

        resp = client.post(
            f"/threads/{thread_id}/messages",
            json={"text": "what about bananas?", "include_code_rag": False},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "receipt" in body
        assert body["assistant"]["role"] == "assistant"
        assert body["assistant"]["text"].startswith("echo:")
        assert body["assembly"]["tokens_assembled"] <= body["assembly"]["tokens_full_thread_est"]
        assert "messages_preview" in body["assembly"]
        assert "messages" not in body["assembly"] or body["assembly"].get("messages") is None


def test_threads_crud_list_get_search_handoff(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
    app = create_app(cfg)
    with TestClient(app) as client:
        app.state.chat_llm = EchoLlm()
        ws_id = _register_workspace(client, tmp_path)

        created = client.post("/threads", json={"workspace_id": ws_id, "title": "t1"})
        assert created.status_code == 201
        thread_id = created.json()["thread"]["id"]

        listed = client.get("/threads", params={"workspace_id": ws_id})
        assert listed.status_code == 200
        rows = listed.json()["threads"]
        assert any(r["id"] == thread_id for r in rows)

        got = client.get(f"/threads/{thread_id}", params={"offset": 0, "limit": 10})
        assert got.status_code == 200
        meta = got.json()
        assert meta["id"] == thread_id
        assert meta["turn_count"] == 0
        assert meta["turns"] == []

        msg = client.post(
            f"/threads/{thread_id}/messages",
            json={"text": "hello mycelium"},
        )
        assert msg.status_code == 200

        got2 = client.get(f"/threads/{thread_id}")
        assert got2.json()["turn_count"] >= 2

        search = client.post(
            f"/threads/{thread_id}/search",
            json={"query": "hello", "limit": 4},
        )
        assert search.status_code == 200
        assert "results" in search.json()

        handoff = client.post(
            f"/threads/{thread_id}/handoff",
            json={"summary": "Ship chat HTTP API"},
        )
        assert handoff.status_code == 200, handoff.text
        body = handoff.json()
        assert body.get("handoff_path") or body.get("path")
        note_body = (body.get("note") or {}).get("body") or ""
        assert "Ship chat HTTP API" in note_body
        assert "hello mycelium" not in note_body or "Ship chat" in note_body


def test_messages_llm_not_configured_error_shape(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
    app = create_app(cfg)
    with TestClient(app) as client:
        # No chat_llm override and no API key → structured ChatError
        app.state.chat_llm = None
        ws_id = _register_workspace(client, tmp_path)
        thread_id = client.post(
            "/threads", json={"workspace_id": ws_id, "title": "no-llm"}
        ).json()["thread"]["id"]

        resp = client.post(
            f"/threads/{thread_id}/messages",
            json={"text": "hi"},
        )
        assert resp.status_code == 400
        err = resp.json()["error"]
        assert err["code"] == "llm_not_configured"
        assert err["message"]


def test_get_unknown_thread_not_found(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
    with TestClient(create_app(cfg)) as client:
        resp = client.get("/threads/thread:does-not-exist")
        assert resp.status_code == 404
        err = resp.json()["error"]
        assert err["code"] == "not_found"


def test_messages_echo_via_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MYCELIUM_LLM", "echo")
    cfg = ensure_test_layout(tmp_path / "home")
    with TestClient(create_app(cfg)) as client:
        ws_id = _register_workspace(client, tmp_path)
        thread_id = client.post(
            "/threads", json={"workspace_id": ws_id}
        ).json()["thread"]["id"]
        resp = client.post(
            f"/threads/{thread_id}/messages",
            json={"text": "env echo path"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["assistant"]["text"].startswith("echo:")
