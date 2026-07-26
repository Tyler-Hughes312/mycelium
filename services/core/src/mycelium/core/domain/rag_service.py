"""Hybrid RAG: vector + FTS + RRF fusion (AD-4 / Stories 3.3–3.4)."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from mycelium.adapters.embeddings.bootstrap import EmbeddingStatus, bootstrap_embedder
from mycelium.adapters.store.edge_store import JsonEdgeStore
from mycelium.adapters.store.symbol_store import JsonSymbolStore
from mycelium.adapters.store.vector_store import JsonVectorStore
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.ports.embedding_runtime import EmbeddingRuntime

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]+|[0-9]+")
_RRF_K = 60


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def rrf_fuse(
    ranked_lists: list[list[str]],
    *,
    k: int = _RRF_K,
) -> dict[str, float]:
    scores: dict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        for rank, node_id in enumerate(ranked, start=1):
            scores[node_id] += 1.0 / (k + rank)
    return dict(scores)


def fts_score(query: str, document: str) -> float:
    q = set(_tokens(query))
    if not q:
        return 0.0
    d = _tokens(document)
    if not d:
        return 0.0
    hits = sum(1 for t in d if t in q)
    coverage = len(q & set(d)) / len(q)
    return hits * 0.15 + coverage


def _normalize_kind(kind: str | None) -> str:
    if not kind:
        return "File"
    k = kind.strip()
    mapping = {
        "symbol": "Symbol",
        "commit": "Commit",
        "note": "Note",
        "file": "File",
    }
    return mapping.get(k.lower(), k if k[:1].isupper() else k.capitalize())


class RagService:
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

    def _require(self, workspace_id: str) -> None:
        if self._workspaces.get(workspace_id) is None:
            raise WorkspaceError("not_found", f"Workspace '{workspace_id}' not found")

    def _ws_dir(self, workspace_id: str) -> Path:
        return self._data_dir / "workspaces" / workspace_id

    def _packet_item(self, row: dict[str, Any], *, score: float, provenance: dict[str, Any]) -> dict[str, Any]:
        meta = dict(row.get("meta") or {})
        kind = _normalize_kind(str(row.get("kind") or meta.get("kind") or "File"))
        title = (
            meta.get("name")
            or meta.get("message")
            or meta.get("path")
            or row.get("node_id")
        )
        path = meta.get("path") or (
            f"sha:{meta['sha'][:7]}" if meta.get("sha") else str(row.get("node_id") or "")
        )
        chip_meta = []
        if meta.get("path"):
            chip_meta.append({"icon": "folder", "text": str(meta["path"])})
        if meta.get("sha"):
            chip_meta.append({"icon": "commit", "text": f"sha:{str(meta['sha'])[:7]}"})
        if meta.get("author"):
            chip_meta.append({"icon": "person", "text": str(meta["author"])})
        return {
            "id": row.get("node_id"),
            "title": title,
            "kind": kind,
            "snippet": (str(row.get("text") or "")[:240]),
            "path": path,
            "score": round(score, 6),
            "meta": chip_meta,
            "provenance": provenance,
        }

    def query(
        self,
        *,
        workspace_id: str,
        query: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        self._require(workspace_id)
        limit = max(1, min(limit, 10))
        store = JsonVectorStore(self._ws_dir(workspace_id))
        rows = store.all_rows()
        if not rows:
            return {
                "query": query,
                "workspace_id": workspace_id,
                "mode": "hybrid_rag",
                "count": 0,
                "results": [],
                "reason": "empty_index",
                "message": "No embeddings yet. Index the workspace and run an embed pass.",
            }

        qvec = self._runtime.embed([query])[0]
        vector_hits = store.search(qvec, limit=min(50, max(limit * 5, 20)))
        vector_ranked = [h["node_id"] for h in vector_hits]

        fts_scored: list[tuple[float, str]] = []
        by_id = {r["node_id"]: r for r in rows}
        for row in rows:
            score = fts_score(query, str(row.get("text") or ""))
            if score > 0:
                fts_scored.append((score, row["node_id"]))
        fts_scored.sort(key=lambda t: t[0], reverse=True)
        fts_ranked = [nid for _, nid in fts_scored[:50]]

        fused = rrf_fuse([vector_ranked, fts_ranked])
        ordered = sorted(fused.items(), key=lambda t: t[1], reverse=True)[:limit]

        vec_rank = {nid: i for i, nid in enumerate(vector_ranked, start=1)}
        fts_rank = {nid: i for i, nid in enumerate(fts_ranked, start=1)}

        results = [
            self._packet_item(
                by_id[node_id],
                score=score,
                provenance={
                    "vector_rank": vec_rank.get(node_id),
                    "fts_rank": fts_rank.get(node_id),
                    "fusion": "rrf",
                },
            )
            for node_id, score in ordered
            if node_id in by_id
        ]

        return {
            "query": query,
            "workspace_id": workspace_id,
            "mode": "hybrid_rag",
            "count": len(results),
            "results": results,
            "embedding": {
                "model_id": self._status.model_id,
                "backend": self._status.backend,
            },
        }

    def focus(
        self,
        *,
        workspace_id: str,
        path: str,
        symbol: str | None = None,
        line: int | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        self._require(workspace_id)
        limit = max(1, min(limit, 10))
        ws_dir = self._ws_dir(workspace_id)
        symbols = JsonSymbolStore(ws_dir).list_all()
        store = JsonVectorStore(ws_dir)
        rows = store.all_rows()

        if not symbols and not rows:
            return {
                "workspace_id": workspace_id,
                "path": path,
                "symbol": symbol,
                "line": line,
                "mode": "focus",
                "count": 0,
                "results": [],
                "reason": "empty_index",
                "message": "Workspace has no indexed symbols or embeddings yet.",
            }

        path_norm = path.replace("\\", "/").lstrip("./")
        candidates = [
            s
            for s in symbols
            if str(s.get("path") or "").replace("\\", "/") == path_norm
            or str(s.get("path") or "").replace("\\", "/").endswith("/" + path_norm)
            or path_norm.endswith("/" + str(s.get("path") or ""))
            or path_norm.endswith(str(s.get("path") or ""))
        ]

        seed: dict[str, Any] | None = None
        if symbol:
            named = [s for s in candidates if str(s.get("name") or "") == symbol]
            if named:
                if line is not None:
                    lined = [
                        s
                        for s in named
                        if int(s.get("start_line") or 0)
                        <= line
                        <= int(s.get("end_line") or 10**9)
                    ]
                    seed = lined[0] if lined else named[0]
                else:
                    seed = named[0]
        if seed is None and candidates:
            if line is not None:
                lined = [
                    s
                    for s in candidates
                    if int(s.get("start_line") or 0)
                    <= line
                    <= int(s.get("end_line") or 10**9)
                ]
                seed = lined[0] if lined else candidates[0]
            else:
                seed = candidates[0]

        seed_id = str(seed.get("id")) if seed else None
        seed_text = (
            f"{seed.get('symbol_kind')} {seed.get('name')} {seed.get('path')}"
            if seed
            else f"file {path} {symbol or ''}"
        )

        graph_neighbors: list[str] = []
        if seed_id:
            edges = JsonEdgeStore(ws_dir).list_all(kind="co_changed")
            for e in edges:
                src, dst = str(e.get("source_id") or ""), str(e.get("target_id") or "")
                if src == seed_id and dst:
                    graph_neighbors.append(dst)
                elif dst == seed_id and src:
                    graph_neighbors.append(src)
            for s in symbols:
                if s.get("path") == seed.get("path") and s.get("id") != seed_id:
                    graph_neighbors.append(str(s["id"]))

        qvec = self._runtime.embed([seed_text])[0]
        vector_hits = store.search(qvec, limit=50) if rows else []
        vector_ranked = [h["node_id"] for h in vector_hits]

        commit_rows = [r for r in rows if _normalize_kind(str(r.get("kind"))) == "Commit"]
        commit_rows.sort(
            key=lambda r: str((r.get("meta") or {}).get("timestamp") or ""),
            reverse=True,
        )
        recency_ranked = [r["node_id"] for r in commit_rows[:50]]

        graph_ranked = list(dict.fromkeys(graph_neighbors))[:50]
        if seed_id:
            graph_ranked = [seed_id] + [n for n in graph_ranked if n != seed_id]

        fused = rrf_fuse([vector_ranked, graph_ranked, recency_ranked])
        if seed_id:
            fused[seed_id] = fused.get(seed_id, 0.0) + 1.0

        by_id = {r["node_id"]: r for r in rows}
        if seed_id and seed_id not in by_id and seed:
            by_id[seed_id] = {
                "node_id": seed_id,
                "kind": "Symbol",
                "text": seed_text,
                "meta": {
                    "name": seed.get("name"),
                    "path": seed.get("path"),
                    "kind": seed.get("symbol_kind"),
                },
            }

        ordered = sorted(fused.items(), key=lambda t: t[1], reverse=True)[:limit]
        results = [
            self._packet_item(
                by_id[node_id],
                score=score,
                provenance={
                    "seed": node_id == seed_id,
                    "graph_proximity": node_id in graph_ranked,
                    "fusion": "rrf",
                    "signals": ["vector", "graph", "recency"],
                },
            )
            for node_id, score in ordered
            if node_id in by_id
        ]

        return {
            "workspace_id": workspace_id,
            "path": path,
            "symbol": symbol,
            "line": line,
            "mode": "focus",
            "seed_id": seed_id,
            "count": len(results),
            "results": results,
            "embedding": {
                "model_id": self._status.model_id,
                "backend": self._status.backend,
            },
        }
