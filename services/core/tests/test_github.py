"""GitHub integration unit tests (mocked HTTP)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from mycelium.adapters.github import GitHubError, GitHubService
from mycelium.adapters.http.app import create_app
from mycelium.adapters.store import JsonFileWorkspaceRepo
from mycelium.core.config import MyceliumConfig, ensure_local_layout


def ensure_test_layout(home: Path) -> MyceliumConfig:
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


def test_github_status_disconnected(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path)
    gh = GitHubService(home=cfg.paths.home, client_id="")
    status = gh.status()
    assert status["connected"] is False
    assert status["oauth_configured"] is False


def test_github_save_pat_and_list(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path)
    gh = GitHubService(home=cfg.paths.home)

    user_res = MagicMock(status_code=200)
    user_res.json.return_value = {"login": "tyler"}
    repos_res = MagicMock(status_code=200)
    repos_res.json.return_value = [
        {
            "id": 1,
            "full_name": "tyler/old-lib",
            "name": "old-lib",
            "private": False,
            "clone_url": "https://github.com/tyler/old-lib.git",
            "ssh_url": "git@github.com:tyler/old-lib.git",
            "html_url": "https://github.com/tyler/old-lib",
            "default_branch": "main",
            "description": "legacy",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    ]

    with patch("mycelium.adapters.github.service.httpx.Client") as client_cls:
        client = MagicMock()
        client_cls.return_value.__enter__.return_value = client
        client.get.side_effect = [user_res, repos_res]
        out = gh.save_pat("ghp_test_token")
        assert out["login"] == "tyler"
        listed = gh.list_repos()
        assert listed["repos"][0]["full_name"] == "tyler/old-lib"

    assert gh.status()["connected"] is True
    gh.disconnect()
    assert gh.status()["connected"] is False


def test_github_device_requires_client_id(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path)
    gh = GitHubService(home=cfg.paths.home, client_id="")
    try:
        gh.device_start()
        raise AssertionError("expected GitHubError")
    except GitHubError as exc:
        assert exc.code == "oauth_not_configured"


def test_github_import_existing_clone(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
    repo = tmp_path / "existing"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    # minimal git so register accepts
    import subprocess

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "i"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    gh = GitHubService(home=cfg.paths.home)
    gh._write_token("tok", auth_mode="pat", login="tyler")
    ws = JsonFileWorkspaceRepo(cfg.paths.data_dir)
    result = gh.import_repo(
        clone_url="https://github.com/tyler/existing.git",
        dest=str(repo),
        full_name="tyler/existing",
        workspace_repo=ws,
    )
    assert result["cloned"] is False
    assert result["workspace"]["path"] == str(repo.resolve())


def test_github_http_status_route(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path)
    with TestClient(create_app(cfg)) as client:
        res = client.get("/integrations/github/status")
        assert res.status_code == 200
        body = res.json()
        assert body["connected"] is False
        settings = client.get("/settings").json()
        assert "github" in settings
