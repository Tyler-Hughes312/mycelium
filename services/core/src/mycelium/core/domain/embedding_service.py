"""Embedding pass over Symbol and Commit Nodes (Story 3.2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mycelium.adapters.embeddings.bootstrap import EmbeddingStatus, bootstrap_embedder
from mycelium.adapters.store.commit_store import JsonCommitStore
from mycelium.adapters.store.symbol_store import JsonSymbolStore
from mycelium.adapters.store.vector_store import JsonVectorStore
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.ports.embedding_runtime import EmbeddingRuntime


def symbol_embed_text(sym: dict[str, Any]) -> str:
    parts = [
        str(sym.get("symbol_kind") or sym.get("kind") or ""),
        str(sym.get("name") or ""),
        str(sym.get("path") or ""),
        str(sym.get("language") or ""),
    ]
    return "\n".join(p for p in parts if p)


def commit_embed_text(commit: dict[str, Any]) -> str:
    paths = commit.get("changed_paths") or commit.get("files") or []
    parts = [
        "commit",
        str(commit.get("message") or ""),
        str(commit.get("author") or ""),
        " ".join(str(p) for p in list(paths)[:40]),
    ]
    return "\n".join(parts)


class EmbeddingService:
    def __init__(
        self,
        *,
        data_dir: Path,
        runtime: EmbeddingRuntime | None = None,
        status: EmbeddingStatus | None = None,
        model: str = "mycelium-hashing-v1",
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

    def _ws_dir(self, workspace_id: str) -> Path:
        return self._data_dir / "workspaces" / workspace_id

    def _require(self, workspace_id: str) -> dict[str, Any]:
        row = self._workspaces.get(workspace_id)
        if row is None:
            raise WorkspaceError("not_found", f"Workspace '{workspace_id}' not found")
        return row

    def embed_workspace(self, workspace_id: str, *, batch_size: int = 32) -> dict[str, Any]:
        self._require(workspace_id)
        ws_dir = self._ws_dir(workspace_id)
        symbols = JsonSymbolStore(ws_dir).list_all()
        commits = JsonCommitStore(ws_dir).list_all()
        store = JsonVectorStore(ws_dir)

        written = 0
        skipped = 0

        def flush(batch: list[tuple[str, str, str, dict[str, Any]]]) -> None:
            nonlocal written, skipped
            if not batch:
                return
            vectors = self._runtime.embed([t for _, _, t, _ in batch])
            for (node_id, kind, text, meta), vec in zip(batch, vectors, strict=True):
                if store.upsert(node_id=node_id, kind=kind, text=text, vector=vec, meta=meta):
                    written += 1
                else:
                    skipped += 1

        batch: list[tuple[str, str, str, dict[str, Any]]] = []
        for sym in symbols:
            node_id = str(sym.get("id") or "")
            if not node_id:
                continue
            text = symbol_embed_text(sym)
            meta = {
                "name": sym.get("name"),
                "path": sym.get("path"),
                "kind": sym.get("symbol_kind") or "Symbol",
                "language": sym.get("language"),
            }
            batch.append((node_id, "Symbol", text, meta))
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
            "commits": len(commits),
            "model": self._status.model_id,
            "backend": self._status.backend,
            "notice": self._status.notice,
        }

    def embed_symbols(
        self,
        workspace_id: str,
        symbols: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Incremental embed for symbol rows (file hook)."""
        self._require(workspace_id)
        store = JsonVectorStore(self._ws_dir(workspace_id))
        written = 0
        skipped = 0
        if not symbols:
            return {"written": 0, "skipped_unchanged": 0, "vectors": store.count()}
        texts = [symbol_embed_text(s) for s in symbols]
        vectors = self._runtime.embed(texts)
        for sym, text, vec in zip(symbols, texts, vectors, strict=True):
            node_id = str(sym.get("id") or "")
            if not node_id:
                continue
            meta = {
                "name": sym.get("name"),
                "path": sym.get("path"),
                "kind": sym.get("symbol_kind") or "Symbol",
                "language": sym.get("language"),
            }
            if store.upsert(node_id=node_id, kind="Symbol", text=text, vector=vec, meta=meta):
                written += 1
            else:
                skipped += 1
        return {"written": written, "skipped_unchanged": skipped, "vectors": store.count()}
