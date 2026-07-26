"""Hybrid RAG: vector + FTS + RRF fusion with typed provenance (AD-4)."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from mycelium.adapters.embeddings.bootstrap import (
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingStatus,
    bootstrap_embedder,
)
from mycelium.adapters.store.edge_store import JsonEdgeStore
from mycelium.adapters.store.symbol_store import JsonSymbolStore
from mycelium.adapters.store.vector_store import JsonVectorStore
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.domain.node_types import (
    display_kind_for_row,
    display_kind_from_symbol_kind,
    embed_type_prefix,
    family_of,
    intent_kinds,
    kind_boost,
)
from mycelium.core.ports.embedding_runtime import EmbeddingRuntime

# Avoid circular import at type-check time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mycelium.core.domain.vault_service import VaultService

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


def _snippet_for(kind: str, text: str, meta: dict[str, Any]) -> str:
    raw = text or ""
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if lines and lines[0].lower().startswith(
        ("code ", "source file", "git commit", "markdown ")
    ):
        lines = lines[1:]
    body = "\n".join(lines).strip()
    if kind == "Commit":
        msg = str(meta.get("message") or body)
        paths = meta.get("changed_paths") or []
        if paths:
            return f"{msg}\nfiles: {', '.join(str(p) for p in paths[:8])}"[:280]
        return msg[:280]
    if kind == "File":
        path = meta.get("path") or ""
        head = body.replace("contents:", "").strip()
        return (f"{path}\n{head}" if path else head)[:280]
    if kind == "Note":
        if "body:" in body:
            body = body.split("body:", 1)[-1].strip()
        title = meta.get("title") or meta.get("name") or ""
        return (f"{title}\n{body}" if title else body)[:280]
    if "source:" in body:
        body = body.split("source:", 1)[-1].strip()
    return body[:280]


def _title_for(kind: str, meta: dict[str, Any], node_id: str | None) -> str:
    if kind == "Commit":
        return str(meta.get("message") or node_id or "commit")
    if kind == "File":
        return str(meta.get("path") or meta.get("name") or node_id or "file")
    if kind == "Note":
        return str(meta.get("title") or meta.get("name") or meta.get("path") or node_id or "note")
    name = meta.get("name")
    if name:
        return str(name)
    return str(meta.get("path") or node_id or kind)


class RagService:
    def __init__(
        self,
        *,
        data_dir: Path,
        runtime: EmbeddingRuntime | None = None,
        status: EmbeddingStatus | None = None,
        model: str = DEFAULT_EMBEDDING_MODEL,
        workspace_repo: JsonFileWorkspaceRepo | None = None,
        vault: VaultService | None = None,
    ) -> None:
        self._data_dir = data_dir
        self._workspaces = workspace_repo or JsonFileWorkspaceRepo(data_dir)
        self._vault = vault
        if runtime is None or status is None:
            runtime, status = bootstrap_embedder(model=model)
        self._runtime = runtime
        self._status = status

    def attach_vault(self, vault: VaultService) -> None:
        self._vault = vault

    def _combined_rows(
        self, workspace_id: str, *, include_vault: bool = True
    ) -> list[dict[str, Any]]:
        rows = list(JsonVectorStore(self._ws_dir(workspace_id)).all_rows())
        if include_vault and self._vault is not None:
            rows.extend(self._vault.all_note_vectors())
        return rows

    def _require(self, workspace_id: str) -> None:
        if self._workspaces.get(workspace_id) is None:
            raise WorkspaceError("not_found", f"Workspace '{workspace_id}' not found")

    def _ws_dir(self, workspace_id: str) -> Path:
        return self._data_dir / "workspaces" / workspace_id

    def _resolve_query_workspace_ids(self, workspace_id: str) -> list[str]:
        """Resolve workspace_id; '*' / 'all' → every registered workspace."""
        key = (workspace_id or "").strip()
        if key in {"*", "all"}:
            ids = [
                str(w["id"])
                for w in self._workspaces.list_workspaces()
                if w.get("id")
            ]
            if not ids:
                raise WorkspaceError(
                    "not_found",
                    "No workspaces registered. Add repos in Library first.",
                )
            return ids
        self._require(key)
        return [key]

    def _workspace_label(self, workspace_id: str) -> dict[str, str]:
        row = self._workspaces.get(workspace_id) or {}
        return {
            "workspace_id": workspace_id,
            "workspace_name": str(row.get("name") or workspace_id[:8]),
            "workspace_path": str(row.get("path") or ""),
        }

    def _packet_item(
        self,
        row: dict[str, Any],
        *,
        score: float,
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        meta = dict(row.get("meta") or {})
        kind = display_kind_for_row(row)
        fam = family_of(kind)
        title = _title_for(kind, meta, row.get("node_id"))
        path = meta.get("path") or (
            f"sha:{str(meta['sha'])[:7]}" if meta.get("sha") else str(row.get("node_id") or "")
        )
        chip_meta: list[dict[str, str]] = []
        chip_meta.append({"icon": "category", "text": kind})
        if meta.get("language"):
            chip_meta.append({"icon": "code", "text": str(meta["language"])})
        if kind in {"Function", "Method", "Class", "Type", "Const", "Symbol"}:
            if meta.get("path"):
                loc = str(meta["path"])
                if meta.get("start_line"):
                    loc = f"{loc}:{meta['start_line']}"
                chip_meta.append({"icon": "folder", "text": loc})
        elif kind == "File" and meta.get("path"):
            chip_meta.append({"icon": "draft", "text": str(meta["path"])})
        elif kind == "Commit":
            if meta.get("sha"):
                chip_meta.append({"icon": "commit", "text": f"sha:{str(meta['sha'])[:7]}"})
            if meta.get("author"):
                chip_meta.append({"icon": "person", "text": str(meta["author"])})
        elif kind == "Note":
            if meta.get("path"):
                chip_meta.append({"icon": "sticky_note_2", "text": str(meta["path"])})
        return {
            "id": row.get("node_id"),
            "title": title,
            "kind": kind,
            "family": fam,
            "snippet": _snippet_for(kind, str(row.get("text") or ""), meta),
            "path": path,
            "start_line": meta.get("start_line"),
            "end_line": meta.get("end_line"),
            "score": round(score, 6),
            "meta": chip_meta,
            "provenance": {
                **provenance,
                "kind": kind,
                "family": fam,
            },
        }

    def query(
        self,
        *,
        workspace_id: str,
        query: str,
        limit: int = 10,
        kinds: list[str] | None = None,
    ) -> dict[str, Any]:
        """Hybrid RAG over one workspace, or all (`workspace_id` = `*` / `all`)."""
        limit = max(1, min(limit, 10))
        ids = self._resolve_query_workspace_ids(workspace_id)
        if len(ids) == 1:
            return self._query_one(
                workspace_id=ids[0],
                query=query,
                limit=limit,
                kinds=kinds,
                include_vault=True,
            )

        # Cross-repo: rank each workspace separately (vault once), merge by score.
        pool: list[dict[str, Any]] = []
        empty_all = True
        for i, wid in enumerate(ids):
            part = self._query_one(
                workspace_id=wid,
                query=query,
                limit=min(10, max(limit, 6)),
                kinds=kinds,
                include_vault=(i == 0),
            )
            if part.get("reason") != "empty_index" and part.get("count", 0) > 0:
                empty_all = False
            label = self._workspace_label(wid)
            for row in part.get("results") or []:
                item = dict(row)
                item.update(label)
                prov = dict(item.get("provenance") or {})
                prov["workspace_id"] = wid
                prov["workspace_name"] = label["workspace_name"]
                item["provenance"] = prov
                meta = list(item.get("meta") or [])
                meta.insert(
                    0,
                    {"icon": "folder_open", "text": label["workspace_name"]},
                )
                item["meta"] = meta
                pool.append(item)

        pool.sort(key=lambda r: float(r.get("score") or 0), reverse=True)
        results = pool[:limit]
        if empty_all and not results:
            return {
                "query": query,
                "workspace_id": "*",
                "workspace_ids": ids,
                "mode": "hybrid_rag",
                "scope": "all_workspaces",
                "count": 0,
                "results": [],
                "reason": "empty_index",
                "message": (
                    "No embeddings across registered workspaces. "
                    "Index each repo in Library / Index first."
                ),
            }
        return {
            "query": query,
            "workspace_id": "*",
            "workspace_ids": ids,
            "mode": "hybrid_rag",
            "scope": "all_workspaces",
            "count": len(results),
            "results": results,
            "intent_kinds": sorted(intent_kinds(query)),
            "embedding": {
                "model_id": self._status.model_id,
                "backend": self._status.backend,
            },
        }

    def _query_one(
        self,
        *,
        workspace_id: str,
        query: str,
        limit: int = 10,
        kinds: list[str] | None = None,
        include_vault: bool = True,
    ) -> dict[str, Any]:
        self._require(workspace_id)
        limit = max(1, min(limit, 10))
        rows = self._combined_rows(workspace_id, include_vault=include_vault)
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

        intents = intent_kinds(query)
        allow = {k.strip() for k in (kinds or []) if k.strip()} or None

        qvec = self._runtime.embed([query])[0]
        # Search workspace + vault note vectors separately then merge ranks
        ws_store = JsonVectorStore(self._ws_dir(workspace_id))
        vector_hits = ws_store.search(qvec, limit=min(80, max(limit * 8, 30)))
        if include_vault and self._vault is not None:
            note_hits = JsonVectorStore(self._data_dir / "vault").search(
                qvec, limit=min(40, max(limit * 4, 15))
            )
            vector_ranked = [h["node_id"] for h in vector_hits]
            for h in note_hits:
                if h["node_id"] not in vector_ranked:
                    vector_ranked.append(h["node_id"])
        else:
            vector_ranked = [h["node_id"] for h in vector_hits]

        fts_scored: list[tuple[float, str]] = []
        by_id = {r["node_id"]: r for r in rows}
        for row in rows:
            score = fts_score(query, str(row.get("text") or ""))
            if score > 0:
                fts_scored.append((score, row["node_id"]))
        fts_scored.sort(key=lambda t: t[0], reverse=True)
        fts_ranked = [nid for _, nid in fts_scored[:80]]

        fused = rrf_fuse([vector_ranked, fts_ranked])
        boosted: list[tuple[str, float]] = []
        for node_id, score in fused.items():
            row = by_id.get(node_id)
            if not row:
                continue
            kind = display_kind_for_row(row)
            if allow and kind not in allow and family_of(kind) not in allow:
                continue
            boosted.append((node_id, score * kind_boost(kind, intents)))
        ordered = sorted(boosted, key=lambda t: t[1], reverse=True)[:limit]

        vec_rank = {nid: i for i, nid in enumerate(vector_ranked, start=1)}
        fts_rank = {nid: i for i, nid in enumerate(fts_ranked, start=1)}
        label = self._workspace_label(workspace_id)

        results = []
        for node_id, score in ordered:
            if node_id not in by_id:
                continue
            item = self._packet_item(
                by_id[node_id],
                score=score,
                provenance={
                    "vector_rank": vec_rank.get(node_id),
                    "fts_rank": fts_rank.get(node_id),
                    "fusion": "rrf",
                    "intent_kinds": sorted(intents) if intents else [],
                    "workspace_id": workspace_id,
                    "workspace_name": label["workspace_name"],
                },
            )
            item.update(label)
            results.append(item)

        return {
            "query": query,
            "workspace_id": workspace_id,
            "mode": "hybrid_rag",
            "scope": "workspace",
            "count": len(results),
            "results": results,
            "intent_kinds": sorted(intents),
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
        rows = self._combined_rows(workspace_id)
        note_rows = self._vault.all_note_vectors() if self._vault else []

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
        seed_kind = (
            display_kind_from_symbol_kind(str(seed.get("symbol_kind") or ""))
            if seed
            else "File"
        )
        seed_text = (
            f"{embed_type_prefix(seed_kind)}\nname: {seed.get('name')}\npath: {seed.get('path')}"
            if seed
            else f"{embed_type_prefix('File')}\npath: {path}"
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
        vector_hits = store.search(qvec, limit=50) if store.count() else []
        vector_ranked = [h["node_id"] for h in vector_hits]
        if note_rows:
            note_store = JsonVectorStore(self._data_dir / "vault")
            for h in note_store.search(qvec, limit=30):
                if h["node_id"] not in vector_ranked:
                    vector_ranked.append(h["node_id"])

        commit_rows = [r for r in rows if display_kind_for_row(r) == "Commit"]
        commit_rows.sort(
            key=lambda r: str((r.get("meta") or {}).get("timestamp") or ""),
            reverse=True,
        )
        recency_ranked = [r["node_id"] for r in commit_rows[:50]]

        graph_ranked = list(dict.fromkeys(graph_neighbors))[:50]
        if seed_id:
            graph_ranked = [seed_id] + [n for n in graph_ranked if n != seed_id]

        # Explicit note→symbol mentions outrank pure similarity (FR-13)
        note_link_ranked: list[str] = []
        if seed_id and self._vault is not None:
            note_link_ranked = self._vault.notes_mentioning(seed_id)
            if symbol:
                for nid in self._vault.notes_mentioning_name(symbol):
                    if nid not in note_link_ranked:
                        note_link_ranked.append(nid)

        fused = rrf_fuse([vector_ranked, graph_ranked, recency_ranked, note_link_ranked])
        if seed_id:
            fused[seed_id] = fused.get(seed_id, 0.0) + 1.0
        for nid in note_link_ranked:
            fused[nid] = fused.get(nid, 0.0) + 0.55

        by_id = {r["node_id"]: r for r in rows}
        if seed_id and seed_id not in by_id and seed:
            by_id[seed_id] = {
                "node_id": seed_id,
                "kind": seed_kind,
                "text": seed_text,
                "meta": {
                    "name": seed.get("name"),
                    "path": seed.get("path"),
                    "kind": seed_kind,
                    "symbol_kind": seed.get("symbol_kind"),
                    "family": "Symbol",
                    "language": seed.get("language"),
                    "start_line": seed.get("start_line"),
                    "end_line": seed.get("end_line"),
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
                    "explicit_note_link": node_id in note_link_ranked,
                    "fusion": "rrf",
                    "signals": ["vector", "graph", "recency", "note_link"],
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
            "seed_kind": seed_kind if seed else None,
            "count": len(results),
            "results": results,
            "embedding": {
                "model_id": self._status.model_id,
                "backend": self._status.backend,
            },
        }
