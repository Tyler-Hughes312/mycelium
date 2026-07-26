"""GitHub integration — device OAuth + PAT, list/import repos (opt-in)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import httpx

log = logging.getLogger("mycelium.github")

DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
API_BASE = "https://api.github.com"
DEFAULT_SCOPE = "repo read:user"


class GitHubError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass
class GitHubService:
    home: Path
    client_id: str = ""

    def __post_init__(self) -> None:
        self.secrets_dir = self.home / "secrets"
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.secrets_dir.chmod(0o700)
        except OSError:
            pass
        env_id = os.environ.get("MYCELIUM_GITHUB_CLIENT_ID", "").strip()
        if env_id:
            self.client_id = env_id

    def _token_path(self) -> Path:
        return self.secrets_dir / "github_token"

    def _meta_path(self) -> Path:
        return self.secrets_dir / "github_meta.json"

    def _device_path(self) -> Path:
        return self.secrets_dir / "github_device.json"

    def status(self) -> dict[str, Any]:
        token = self.read_token()
        meta = self._read_meta()
        return {
            "connected": bool(token),
            "login": meta.get("login"),
            "auth_mode": meta.get("auth_mode"),
            "oauth_configured": bool(self.client_id),
            "client_id_set": bool(self.client_id),
            "repos_clone_root": str(self.home / "repos"),
        }

    def read_token(self) -> str | None:
        path = self._token_path()
        if not path.is_file():
            return None
        raw = path.read_text(encoding="utf-8").strip()
        return raw or None

    def _read_meta(self) -> dict[str, Any]:
        path = self._meta_path()
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_token(self, token: str, *, auth_mode: str, login: str | None = None) -> None:
        path = self._token_path()
        path.write_text(token.strip() + "\n", encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        meta = {"auth_mode": auth_mode, "login": login, "updated_at": int(time.time())}
        self._meta_path().write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        try:
            self._meta_path().chmod(0o600)
        except OSError:
            pass

    def disconnect(self) -> dict[str, Any]:
        for p in (self._token_path(), self._meta_path(), self._device_path()):
            if p.is_file():
                p.unlink()
        return {"connected": False}

    def save_pat(self, token: str) -> dict[str, Any]:
        token = token.strip()
        if not token:
            raise GitHubError("invalid_token", "Token is empty")
        user = self._fetch_user(token)
        self._write_token(token, auth_mode="pat", login=user.get("login"))
        return {"connected": True, "login": user.get("login"), "auth_mode": "pat"}

    def device_start(self) -> dict[str, Any]:
        if not self.client_id:
            raise GitHubError(
                "oauth_not_configured",
                "Set github.client_id in ~/.mycelium/config.toml or "
                "MYCELIUM_GITHUB_CLIENT_ID, or paste a Personal Access Token instead.",
            )
        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                DEVICE_CODE_URL,
                data={"client_id": self.client_id, "scope": DEFAULT_SCOPE},
                headers={"Accept": "application/json"},
            )
        if res.status_code >= 400:
            raise GitHubError("device_start_failed", res.text[:300])
        data = res.json()
        if "error" in data:
            raise GitHubError(str(data.get("error")), str(data.get("error_description", data)))
        pending = {
            "device_code": data["device_code"],
            "interval": int(data.get("interval", 5)),
            "expires_at": int(time.time()) + int(data.get("expires_in", 900)),
            "user_code": data["user_code"],
            "verification_uri": data.get("verification_uri")
            or data.get("verification_uri_complete")
            or "https://github.com/login/device",
        }
        self._device_path().write_text(json.dumps(pending) + "\n", encoding="utf-8")
        try:
            self._device_path().chmod(0o600)
        except OSError:
            pass
        return {
            "user_code": pending["user_code"],
            "verification_uri": pending["verification_uri"],
            "interval": pending["interval"],
            "expires_in": max(0, pending["expires_at"] - int(time.time())),
        }

    def device_poll(self) -> dict[str, Any]:
        if not self.client_id:
            raise GitHubError("oauth_not_configured", "OAuth client_id is not configured")
        path = self._device_path()
        if not path.is_file():
            raise GitHubError("no_pending_device", "Start device login first")
        pending = json.loads(path.read_text(encoding="utf-8"))
        if int(time.time()) > int(pending.get("expires_at", 0)):
            path.unlink(missing_ok=True)
            raise GitHubError("device_expired", "Device code expired — start again")

        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                ACCESS_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "device_code": pending["device_code"],
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            )
        # GitHub may return form or JSON
        if "application/json" in res.headers.get("content-type", ""):
            data = res.json()
        else:
            parsed = parse_qs(res.text)
            data = {k: v[0] for k, v in parsed.items()}

        err = data.get("error")
        if err == "authorization_pending":
            return {"status": "pending", "interval": pending.get("interval", 5)}
        if err == "slow_down":
            return {"status": "pending", "interval": int(pending.get("interval", 5)) + 5}
        if err == "expired_token":
            path.unlink(missing_ok=True)
            raise GitHubError("device_expired", "Device code expired — start again")
        if err == "access_denied":
            path.unlink(missing_ok=True)
            raise GitHubError("access_denied", "GitHub authorization was denied")
        if err:
            raise GitHubError(str(err), str(data.get("error_description", err)))

        token = data.get("access_token")
        if not token:
            raise GitHubError("token_missing", "No access_token in GitHub response")
        user = self._fetch_user(token)
        self._write_token(token, auth_mode="oauth_device", login=user.get("login"))
        path.unlink(missing_ok=True)
        return {
            "status": "connected",
            "connected": True,
            "login": user.get("login"),
            "auth_mode": "oauth_device",
        }

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Mycelium-Local",
        }

    def _fetch_user(self, token: str) -> dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            res = client.get(f"{API_BASE}/user", headers=self._headers(token))
        if res.status_code == 401:
            raise GitHubError("unauthorized", "GitHub token rejected")
        if res.status_code >= 400:
            raise GitHubError("api_error", res.text[:300])
        return res.json()

    def list_repos(self, *, page: int = 1, per_page: int = 30) -> dict[str, Any]:
        token = self.read_token()
        if not token:
            raise GitHubError("not_connected", "Connect GitHub in Settings first")
        page = max(1, page)
        per_page = max(1, min(per_page, 100))
        with httpx.Client(timeout=45.0) as client:
            res = client.get(
                f"{API_BASE}/user/repos",
                headers=self._headers(token),
                params={
                    "page": page,
                    "per_page": per_page,
                    "sort": "updated",
                    "affiliation": "owner,collaborator,organization_member",
                },
            )
        if res.status_code == 401:
            raise GitHubError("unauthorized", "GitHub token rejected — reconnect")
        if res.status_code >= 400:
            raise GitHubError("api_error", res.text[:300])
        rows = []
        for r in res.json():
            rows.append(
                {
                    "id": r.get("id"),
                    "full_name": r.get("full_name"),
                    "name": r.get("name"),
                    "private": bool(r.get("private")),
                    "clone_url": r.get("clone_url"),
                    "ssh_url": r.get("ssh_url"),
                    "html_url": r.get("html_url"),
                    "default_branch": r.get("default_branch"),
                    "description": r.get("description") or "",
                    "updated_at": r.get("updated_at"),
                }
            )
        return {"repos": rows, "page": page, "per_page": per_page}

    def import_repo(
        self,
        *,
        clone_url: str,
        dest: str | None = None,
        full_name: str | None = None,
        workspace_repo: Any,
    ) -> dict[str, Any]:
        token = self.read_token()
        if not token:
            raise GitHubError("not_connected", "Connect GitHub in Settings first")
        clone_url = clone_url.strip()
        if not clone_url:
            raise GitHubError("invalid_url", "clone_url is required")

        name = (full_name or Path(clone_url.rstrip("/").removesuffix(".git")).name).replace(
            "/", "__"
        )
        if dest:
            target = Path(dest).expanduser()
        else:
            target = self.home / "repos" / name
        target.parent.mkdir(parents=True, exist_ok=True)

        cloned = False
        if target.exists() and (target / ".git").is_dir():
            log.info("import: existing clone at %s", target)
        elif target.exists():
            raise GitHubError(
                "dest_exists",
                f"Destination exists and is not a git repo: {target}",
            )
        else:
            # Prefer HTTPS with token for private repos without SSH keys.
            auth_url = clone_url
            if clone_url.startswith("https://github.com/"):
                auth_url = clone_url.replace(
                    "https://github.com/",
                    f"https://x-access-token:{token}@github.com/",
                    1,
                )
            try:
                subprocess.run(
                    ["git", "clone", auth_url, str(target)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
            except subprocess.CalledProcessError as exc:
                raise GitHubError(
                    "clone_failed",
                    (exc.stderr or exc.stdout or str(exc))[:500],
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise GitHubError("clone_timeout", "git clone timed out") from exc
            cloned = True
            # Scrub token from remote URL
            try:
                subprocess.run(
                    ["git", "-C", str(target), "remote", "set-url", "origin", clone_url],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                pass

        row = workspace_repo.register(str(target.resolve()))
        return {
            "workspace": row,
            "path": str(target.resolve()),
            "cloned": cloned,
            "full_name": full_name,
        }
