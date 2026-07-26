"""HTTP client used by the MCP bridge — same Core API as Desktop / Editor."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_CORE_URL = os.environ.get("MYCELIUM_CORE_URL", "http://127.0.0.1:8787")


class CoreHttp:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        if client is not None:
            self._client = client
            self._owns_client = False
            self.base_url = str(client.base_url).rstrip("/")
        else:
            self.base_url = (base_url or DEFAULT_CORE_URL).rstrip("/")
            self._client = httpx.Client(base_url=self.base_url, timeout=timeout)
            self._owns_client = True

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def list_workspaces(self) -> list[dict[str, Any]]:
        return list(self._get("/workspaces").get("workspaces") or [])

    def query(
        self,
        *,
        query: str,
        workspace_id: str,
        limit: int = 8,
        kinds: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "query": query,
            "workspace_id": workspace_id,
            "limit": limit,
        }
        if kinds:
            body["kinds"] = kinds
        return self._post("/query", body)

    def focus(
        self,
        *,
        workspace_id: str,
        path: str,
        symbol: str | None = None,
        line: int | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "workspace_id": workspace_id,
            "path": path,
            "limit": limit,
        }
        if symbol:
            body["symbol"] = symbol
        if line is not None:
            body["line"] = line
        return self._post("/context/focus", body)

    def get_note(self, note_id: str) -> dict[str, Any]:
        from urllib.parse import quote

        stem = note_id[5:] if note_id.startswith("note:") else note_id
        # Encode each segment; keep "/" so FastAPI {note_id:path} matches nested notes
        encoded = "/".join(quote(part, safe="") for part in stem.split("/"))
        return self._get(f"/vault/notes/{encoded}").get("note") or {}

    def list_notes(self) -> list[dict[str, Any]]:
        return list(self._get("/vault/notes").get("notes") or [])

    def create_note(
        self,
        *,
        title: str,
        body: str = "",
        bucket: str | None = None,
        filename: str | None = None,
        link_symbol: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"title": title, "body": body}
        if bucket:
            payload["bucket"] = bucket
        if filename:
            payload["filename"] = filename
        if link_symbol:
            payload["link_symbol"] = link_symbol
        return self._post("/vault/notes", payload).get("note") or {}

    def update_note(
        self,
        note_id: str,
        *,
        title: str | None = None,
        body: str | None = None,
    ) -> dict[str, Any]:
        from urllib.parse import quote

        stem = note_id[5:] if note_id.startswith("note:") else note_id
        encoded = "/".join(quote(part, safe="") for part in stem.split("/"))
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        return self._put(f"/vault/notes/{encoded}", payload).get("note") or {}

    def create_bucket(self, name: str) -> dict[str, Any]:
        return self._post("/vault/buckets", {"name": name}).get("bucket") or {}

    def vault_scaffold(self) -> dict[str, Any]:
        return self._post("/vault/scaffold", {}).get("scaffold") or {}

    def vault_tree(self) -> dict[str, Any]:
        return self._get("/vault/tree")

    def vault_pack(
        self,
        *,
        bucket: str | None = None,
        max_tokens: int = 2000,
        include_bodies: bool = True,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "max_tokens": max_tokens,
            "include_bodies": include_bodies,
        }
        if bucket:
            body["bucket"] = bucket
        return self._post("/vault/pack", body).get("pack") or {}

    def list_commits(self, workspace_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        return list(
            self._get(f"/workspaces/{workspace_id}/commits", params={"limit": limit}).get(
                "commits"
            )
            or []
        )

    def sync_workspace(self, workspace_id: str) -> dict[str, Any]:
        return self._post(f"/workspaces/{workspace_id}/sync", {}).get("sync") or {}

    def vault_reindex(self, workspace_id: str | None = None) -> dict[str, Any]:
        params = {"workspace_id": workspace_id} if workspace_id else None
        res = self._client.post("/vault/reindex", params=params)
        res.raise_for_status()
        return res.json().get("reindex") or {}

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        res = self._client.get(path, params=params)
        res.raise_for_status()
        return res.json()

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        res = self._client.post(path, json=body)
        res.raise_for_status()
        return res.json()

    def _put(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        res = self._client.put(path, json=body)
        res.raise_for_status()
        return res.json()
