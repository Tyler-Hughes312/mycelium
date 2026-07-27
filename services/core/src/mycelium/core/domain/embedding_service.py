"""Embedding pass over typed Nodes: Function/Class/File/Commit/… (Story 3.2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mycelium.adapters.embeddings.bootstrap import (
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingStatus,
    bootstrap_embedder,
)
from mycelium.adapters.store.commit_store import JsonCommitStore
from mycelium.adapters.store.symbol_store import JsonSymbolStore
from mycelium.adapters.store.vector_store import JsonVectorStore
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.domain.node_types import (
    display_kind_from_symbol_kind,
    embed_type_prefix,
)
from mycelium.core.ports.embedding_runtime import EmbeddingRuntime

_MAX_SNIPPET_CHARS = 1200
_MAX_FILE_CHARS = 1500


def _read_symbol_snippet(repo_path: Path | None, sym: dict[str, Any]) -> str:
    if repo_path is None:
        return ""
    rel = str(sym.get("path") or "")
    if not rel:
        return ""
    abs_path = repo_path / rel
    if not abs_path.is_file():
        return ""
    try:
        lines = abs_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    start = max(int(sym.get("start_line") or 1) - 1, 0)
    end = int(sym.get("end_line") or start + 1)
    end = max(end, start + 1)
    if end - start > 80:
        end = start + 80
    snippet = "\n".join(lines[start:end]).strip()
    if len(snippet) > _MAX_SNIPPET_CHARS:
        snippet = snippet[:_MAX_SNIPPET_CHARS] + "\n…"
    return snippet


def _read_file_head(repo_path: Path | None, path: str) -> str:
    if repo_path is None or not path:
        return ""
    abs_path = repo_path / path
    if not abs_path.is_file():
        return ""
    try:
        text = abs_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    head = "\n".join(text.splitlines()[:60]).strip()
    if len(head) > _MAX_FILE_CHARS:
        head = head[:_MAX_FILE_CHARS] + "\n…"
    return head


def symbol_display_kind(sym: dict[str, Any]) -> str:
    return display_kind_from_symbol_kind(
        str(sym.get("symbol_kind") or sym.get("kind") or "symbol")
    )


def symbol_embed_text(
    sym: dict[str, Any],
    *,
    repo_path: Path | None = None,
) -> str:
    kind = symbol_display_kind(sym)
    name = str(sym.get("name") or "")
    path = str(sym.get("path") or "")
    lang = str(sym.get("language") or "")
    start = sym.get("start_line")
    end = sym.get("end_line")
    snippet = _read_symbol_snippet(repo_path, sym)
    loc = f"lines {start}-{end}" if start is not None else ""
    parts = [
        embed_type_prefix(kind),
        f"name: {name}" if name else "",
        f"path: {path}" if path else "",
        f"language: {lang}" if lang else "",
        loc,
        "source:",
        snippet,
    ]
    return "\n".join(p for p in parts if p)


def file_embed_text(file_row: dict[str, Any], *, repo_path: Path | None = None) -> str:
    path = str(file_row.get("path") or "")
    lang = str(file_row.get("language") or "unknown")
    head = _read_file_head(repo_path, path)
    parts = [
        embed_type_prefix("File"),
        f"path: {path}",
        f"language: {lang}",
        "contents:",
        head or "(empty or unreadable)",
    ]
    return "\n".join(parts)


def commit_embed_text(commit: dict[str, Any]) -> str:
    paths = commit.get("changed_paths") or commit.get("files") or []
    parts = [
        embed_type_prefix("Commit"),
        f"message: {commit.get('message') or ''}",
        f"author: {commit.get('author')}" if commit.get("author") else "",
        f"timestamp: {commit.get('timestamp')}" if commit.get("timestamp") else "",
        f"sha: {commit.get('hash')}" if commit.get("hash") else "",
        "changed files: " + ", ".join(str(p) for p in list(paths)[:40]),
    ]
    return "\n".join(p for p in parts if p)


class EmbeddingService:
    def __init__(
        self,
        *,
        data_dir: Path,
        runtime: EmbeddingRuntime | None = None,
        status: EmbeddingStatus | None = None,
        model: str = DEFAULT_EMBEDDING_MODEL,
        workspace_repo: JsonFileWorkspaceRepo | None = None,
    ) -> None:
        self._data_dir = data_dir
        self._workspaces = workspace_repo or JsonFileWorkspaceRepo(data_dir)
        if runtime is None or status is None:
            runtime, status = bootstrap_embedder(model=model)
        self._runtime = runtime
        self._status = status

    @property
    def status(self) -> EmbeddingStatus:
        return self._status

    @property
    def runtime(self) -> EmbeddingRuntime:
        return self._runtime

    def _ws_dir(self, workspace_id: str) -> Path:
        return self._data_dir / "workspaces" / workspace_id

    def _require(self, workspace_id: str) -> dict[str, Any]:
        row = self._workspaces.get(workspace_id)
        if row is None:
            raise WorkspaceError("not_found", f"Workspace '{workspace_id}' not found")
        return row

    def _repo_path(self, workspace_id: str) -> Path | None:
        row = self._workspaces.get(workspace_id)
        if not row:
            return None
        path = Path(str(row.get("path") or ""))
        return path if path.is_dir() else None

    def embed_workspace(self, workspace_id: str, *, batch_size: int = 32) -> dict[str, Any]:
        self._require(workspace_id)
        ws_dir = self._ws_dir(workspace_id)
        repo_path = self._repo_path(workspace_id)
        symbol_store = JsonSymbolStore(ws_dir)
        symbols = symbol_store.list_all()
        files = symbol_store.list_files(limit=100_000)
        commits = JsonCommitStore(ws_dir).list_all()
        store = JsonVectorStore(ws_dir)
        model_id = self._status.model_id

        written = 0
        skipped = 0

        def flush(batch: list[tuple[str, str, str, dict[str, Any]]]) -> None:
            nonlocal written, skipped
            if not batch:
                return
            vectors = self._runtime.embed([t for _, _, t, _ in batch])
            rows = [
                {
                    "node_id": node_id,
                    "kind": kind,
                    "text": text,
                    "vector": vec,
                    "model_id": model_id,
                    "meta": meta,
                }
                for (node_id, kind, text, meta), vec in zip(batch, vectors, strict=True)
            ]
            w, s = store.upsert_many(rows)
            written += w
            skipped += s

        batch: list[tuple[str, str, str, dict[str, Any]]] = []

        for sym in symbols:
            node_id = str(sym.get("id") or "")
            if not node_id:
                continue
            kind = symbol_display_kind(sym)
            text = symbol_embed_text(sym, repo_path=repo_path)
            meta = {
                "name": sym.get("name"),
                "path": sym.get("path"),
                "kind": kind,
                "symbol_kind": sym.get("symbol_kind"),
                "family": "Symbol",
                "language": sym.get("language"),
                "start_line": sym.get("start_line"),
                "end_line": sym.get("end_line"),
            }
            batch.append((node_id, kind, text, meta))
            if len(batch) >= batch_size:
                flush(batch)
                batch = []
        flush(batch)
        batch = []

        for file_row in files:
            node_id = str(file_row.get("id") or "")
            if not node_id:
                continue
            text = file_embed_text(file_row, repo_path=repo_path)
            meta = {
                "name": Path(str(file_row.get("path") or "")).name,
                "path": file_row.get("path"),
                "kind": "File",
                "family": "File",
                "language": file_row.get("language"),
            }
            batch.append((node_id, "File", text, meta))
            if len(batch) >= batch_size:
                flush(batch)
                batch = []
        flush(batch)
        batch = []

        for commit in commits:
            node_id = str(commit.get("id") or "")
            if not node_id:
                continue
            text = commit_embed_text(commit)
            meta = {
                "sha": commit.get("hash"),
                "message": commit.get("message"),
                "author": commit.get("author"),
                "timestamp": commit.get("timestamp"),
                "kind": "Commit",
                "family": "Commit",
                "changed_paths": list(commit.get("changed_paths") or [])[:20],
            }
            batch.append((node_id, "Commit", text, meta))
            if len(batch) >= batch_size:
                flush(batch)
                batch = []
        flush(batch)

        return {
            "workspace_id": workspace_id,
            "vectors": store.count(),
            "written": written,
            "skipped_unchanged": skipped,
            "symbols": len(symbols),
            "files": len(files),
            "commits": len(commits),
            "model": model_id,
            "backend": self._status.backend,
            "notice": self._status.notice,
        }

    def embed_symbols(
        self,
        workspace_id: str,
        symbols: list[dict[str, Any]],
        *,
        file_node: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Incremental embed for symbol rows (+ optional file node)."""
        self._require(workspace_id)
        store = JsonVectorStore(self._ws_dir(workspace_id))
        repo_path = self._repo_path(workspace_id)
        model_id = self._status.model_id
        written = 0
        skipped = 0

        items: list[tuple[str, str, str, dict[str, Any]]] = []
        for sym in symbols:
            node_id = str(sym.get("id") or "")
            if not node_id:
                continue
            kind = symbol_display_kind(sym)
            text = symbol_embed_text(sym, repo_path=repo_path)
            meta = {
                "name": sym.get("name"),
                "path": sym.get("path"),
                "kind": kind,
                "symbol_kind": sym.get("symbol_kind"),
                "family": "Symbol",
                "language": sym.get("language"),
                "start_line": sym.get("start_line"),
                "end_line": sym.get("end_line"),
            }
            items.append((node_id, kind, text, meta))

        if file_node and file_node.get("id"):
            text = file_embed_text(file_node, repo_path=repo_path)
            items.append(
                (
                    str(file_node["id"]),
                    "File",
                    text,
                    {
                        "name": Path(str(file_node.get("path") or "")).name,
                        "path": file_node.get("path"),
                        "kind": "File",
                        "family": "File",
                        "language": file_node.get("language"),
                    },
                )
            )

        if not items:
            return {"written": 0, "skipped_unchanged": 0, "vectors": store.count()}

        vectors = self._runtime.embed([t for _, _, t, _ in items])
        rows = [
            {
                "node_id": node_id,
                "kind": kind,
                "text": text,
                "vector": vec,
                "model_id": model_id,
                "meta": meta,
            }
            for (node_id, kind, text, meta), vec in zip(items, vectors, strict=True)
        ]
        written, skipped = store.upsert_many(rows)
        return {"written": written, "skipped_unchanged": skipped, "vectors": store.count()}

    def upsert_nodes(
        self,
        workspace_id: str,
        nodes: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """Embed and upsert arbitrary nodes into the workspace vector store.

        Each node: ``id`` or ``node_id``, ``kind``, ``text``, optional ``meta``.
        Returns ``(written, skipped_unchanged)``.
        """
        self._require(workspace_id)
        if not nodes:
            return 0, 0
        store = JsonVectorStore(self._ws_dir(workspace_id))
        model_id = self._status.model_id
        prepared: list[tuple[str, str, str, dict[str, Any]]] = []
        for node in nodes:
            node_id = str(node.get("node_id") or node.get("id") or "")
            if not node_id:
                continue
            kind = str(node.get("kind") or "Unknown")
            text = str(node.get("text") or "")
            meta = dict(node.get("meta") or {})
            prepared.append((node_id, kind, text, meta))
        if not prepared:
            return 0, 0
        vectors = self._runtime.embed([t for _, _, t, _ in prepared])
        rows = [
            {
                "node_id": node_id,
                "kind": kind,
                "text": text,
                "vector": vec,
                "model_id": model_id,
                "meta": meta,
            }
            for (node_id, kind, text, meta), vec in zip(prepared, vectors, strict=True)
        ]
        return store.upsert_many(rows)
