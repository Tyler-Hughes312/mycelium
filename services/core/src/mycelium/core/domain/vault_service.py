"""Thinking Vault domain — CRUD, wikilinks, backlinks, note embeddings (E4)."""

from __future__ import annotations

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
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo
from mycelium.adapters.vault.fs import NoteRecord, VaultError, VaultFs
from mycelium.adapters.vault.scaffold import scaffold_vault
from mycelium.adapters.vault.wikilinks import parse_wikilinks
from mycelium.core.domain.node_types import embed_type_prefix
from mycelium.core.ports.embedding_runtime import EmbeddingRuntime

_VAULT_EDGE_KINDS = {"wikilink", "mentions"}


def estimate_tokens(text: str) -> int:
    """Cheap char/4 token estimate — no tiktoken dependency."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def note_embed_text(note: NoteRecord) -> str:
    parts = [
        embed_type_prefix("Note"),
        f"title: {note.title}",
        f"path: {note.path}",
    ]
    if note.bucket:
        parts.append(f"bucket: {note.bucket}")
    if note.is_index:
        parts.append("role: bucket_index")
    parts.extend(["body:", note.body[:4000]])
    return "\n".join(parts)


def note_to_dict(note: NoteRecord, *, links: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": note.id,
        "kind": "Note",
        "family": "Note",
        "title": note.title,
        "path": note.path,
        "abs_path": note.abs_path,
        "body": note.body,
        "updated_at": note.updated_at,
        "bucket": note.bucket,
        "is_index": note.is_index,
    }
    if links is not None:
        payload.update(links)
    return payload


class VaultService:
    def __init__(
        self,
        *,
        vault_dir: Path,
        data_dir: Path,
        workspace_repo: JsonFileWorkspaceRepo | None = None,
        runtime: EmbeddingRuntime | None = None,
        status: EmbeddingStatus | None = None,
        model: str = DEFAULT_EMBEDDING_MODEL,
    ) -> None:
        self._vault = VaultFs(vault_dir)
        self._data_dir = data_dir
        self._meta_dir = data_dir / "vault"
        self._meta_dir.mkdir(parents=True, exist_ok=True)
        self._edges = JsonEdgeStore(self._meta_dir)
        self._vectors = JsonVectorStore(self._meta_dir)
        self._workspaces = workspace_repo or JsonFileWorkspaceRepo(data_dir)
        if runtime is None or status is None:
            runtime, status = bootstrap_embedder(model=model)
        self._runtime = runtime
        self._status = status

    @property
    def vault_dir(self) -> Path:
        return self._vault.root

    @property
    def status(self) -> EmbeddingStatus:
        return self._status

    def info(self) -> dict[str, Any]:
        notes = self._vault.list_notes()
        return {
            "path": str(self._vault.root),
            "notes": len(notes),
            "edges": self._edges.count(),
            "vectors": self._vectors.count(),
            "embedding": {
                "model_id": self._status.model_id,
                "backend": self._status.backend,
            },
        }

    def list_notes(self) -> list[dict[str, Any]]:
        return [note_to_dict(n, links=self._link_meta(n.id, n.body)) for n in self._vault.list_notes()]

    def list_tree(self) -> dict[str, Any]:
        """Structure-first vault map — no embeddings."""
        return self._vault.list_tree()

    def create_bucket(self, name: str) -> dict[str, Any]:
        result = self._vault.mkdir_bucket(name)
        index_path = result.get("index") or {}
        index_id = index_path.get("id")
        if index_id:
            try:
                note = self._vault.get(str(index_id))
                self._index_note(note)
            except VaultError:
                pass
        return result

    def ensure_scaffold(self) -> dict[str, Any]:
        """Apply kepano/obsidian-mind inspired layout (idempotent)."""
        result = scaffold_vault(self._vault.root)
        # Reindex new seed notes into edges/vectors
        self.reindex()
        return result

    def get_note(self, note_id: str) -> dict[str, Any]:
        note = self._vault.get(note_id)
        return note_to_dict(note, links=self._link_meta(note.id, note.body))

    def create_note(
        self,
        *,
        title: str,
        body: str = "",
        filename: str | None = None,
        link_symbol: str | None = None,
        bucket: str | None = None,
    ) -> dict[str, Any]:
        if link_symbol and f"[[{link_symbol}]]" not in body:
            body = f"Linked symbol: [[{link_symbol}]]\n\n{body}".rstrip() + "\n"
        note = self._vault.create(
            title=title, body=body, filename=filename, bucket=bucket
        )
        self._index_note(note)
        return note_to_dict(note, links=self._link_meta(note.id, note.body))

    def pack(
        self,
        *,
        bucket: str | None = None,
        max_tokens: int = 2000,
        include_bodies: bool = True,
    ) -> dict[str, Any]:
        """
        Deterministic token-budget pack for LLMs — never calls embeddings/RAG.

        Fill order: title map → `_index` bodies → remaining note bodies (truncate last).
        """
        max_tokens = max(64, min(int(max_tokens), 100_000))
        notes = self._vault.notes_in_bucket(bucket)
        scope = bucket.strip() if bucket else "(vault root)"
        included: list[dict[str, Any]] = []
        parts: list[str] = [f"# Mycelium vault pack — {scope}", ""]

        # 1) Compact map (titles only)
        map_lines = ["## Map", ""]
        for n in notes:
            marker = " (index)" if n.is_index else ""
            map_lines.append(f"- `{n.path}` — {n.title}{marker}")
        map_text = "\n".join(map_lines) + "\n"
        used = estimate_tokens(map_text)
        if used > max_tokens:
            # Extreme tight budget: truncate map
            budget_chars = max_tokens * 4
            map_text = map_text[:budget_chars]
            used = estimate_tokens(map_text)
            parts.append(map_text)
            included.append({"phase": "map", "truncated": True})
            return {
                "text": "\n".join(parts).rstrip() + "\n",
                "tokens_est": used,
                "max_tokens": max_tokens,
                "bucket": bucket or "",
                "included": included,
                "truncated": True,
            }
        parts.append(map_text)
        included.append({"phase": "map", "notes": len(notes)})

        if not include_bodies:
            text = "\n".join(parts).rstrip() + "\n"
            return {
                "text": text,
                "tokens_est": estimate_tokens(text),
                "max_tokens": max_tokens,
                "bucket": bucket or "",
                "included": included,
                "truncated": False,
            }

        indexes = [n for n in notes if n.is_index]
        others = [n for n in notes if not n.is_index]
        truncated = False

        def append_note(note: NoteRecord, *, phase: str) -> bool:
            nonlocal used, truncated
            header = f"## {note.title}\n\n_path: `{note.path}`_\n\n"
            body = (note.body or "").rstrip() + "\n"
            block = header + body
            cost = estimate_tokens(block)
            remaining = max_tokens - used
            if remaining <= 0:
                truncated = True
                return False
            if cost <= remaining:
                parts.append(block)
                used += cost
                included.append(
                    {"phase": phase, "id": note.id, "path": note.path, "tokens_est": cost}
                )
                return True
            # Truncate last body to fit
            header_cost = estimate_tokens(header)
            body_budget = max(0, remaining - header_cost) * 4
            if body_budget < 40:
                truncated = True
                return False
            clipped = body[:body_budget].rstrip() + "\n\n…[truncated]\n"
            block = header + clipped
            parts.append(block)
            used += estimate_tokens(block)
            included.append(
                {
                    "phase": phase,
                    "id": note.id,
                    "path": note.path,
                    "tokens_est": estimate_tokens(block),
                    "truncated": True,
                }
            )
            truncated = True
            return False

        for note in indexes:
            if not append_note(note, phase="index"):
                break
        if not truncated:
            for note in others:
                if not append_note(note, phase="body"):
                    break

        text = "\n".join(parts).rstrip() + "\n"
        return {
            "text": text,
            "tokens_est": estimate_tokens(text),
            "max_tokens": max_tokens,
            "bucket": bucket or "",
            "included": included,
            "truncated": truncated,
        }

    def update_note(
        self,
        note_id: str,
        *,
        title: str | None = None,
        body: str | None = None,
    ) -> dict[str, Any]:
        note = self._vault.update(note_id, title=title, body=body)
        self._index_note(note)
        return note_to_dict(note, links=self._link_meta(note.id, note.body))

    def delete_note(self, note_id: str) -> None:
        self._vault.delete(note_id)
        self._edges.delete_by_source(note_id, kinds=_VAULT_EDGE_KINDS)
        self._vectors.delete(note_id)

    def reindex_path(self, abs_or_rel: str) -> dict[str, Any] | None:
        """Incremental vault note re-embed from a filesystem path (watcher)."""
        path = Path(abs_or_rel).expanduser()
        try:
            rel = path.resolve().relative_to(self._vault.root)
        except ValueError:
            return None
        if rel.suffix.lower() != ".md":
            return None
        note_id = f"note:{rel.with_suffix('').as_posix()}"
        if not path.is_file():
            self._edges.delete_by_source(note_id, kinds=_VAULT_EDGE_KINDS)
            self._vectors.delete(note_id)
            return {"deleted": True, "id": note_id}
        try:
            note = self._vault.get(note_id)
        except VaultError:
            return None
        self._index_note(note)
        return {"id": note.id, "path": note.path, "indexed": True}

    def backlinks(self, note_id: str) -> dict[str, Any]:
        """Notes (and optionally symbols) that link to this note."""
        # ensure note exists
        note = self._vault.get(note_id)
        rows = []
        for edge in self._edges.list_all(kind="wikilink"):
            if edge.get("target_id") != note_id:
                continue
            src = str(edge.get("source_id") or "")
            try:
                src_note = self._vault.get(src)
            except VaultError:
                continue
            excerpt = self._excerpt_around(src_note.body, note.title) or self._excerpt_around(
                src_note.body, Path(note.path).stem
            )
            rows.append(
                {
                    "id": src_note.id,
                    "title": src_note.title,
                    "path": src_note.path,
                    "excerpt": excerpt,
                    "edge_id": edge.get("id"),
                }
            )
        return {
            "note_id": note.id,
            "title": note.title,
            "count": len(rows),
            "backlinks": rows,
        }

    def reindex(self, *, workspace_id: str | None = None) -> dict[str, Any]:
        """Rebuild wikilink/mentions edges + note embeddings from disk."""
        notes = self._vault.list_notes()
        all_edges: list[dict[str, Any]] = []
        unresolved_total = 0
        for note in notes:
            edges, unresolved = self._resolve_links(note, workspace_id=workspace_id)
            all_edges.extend(edges)
            unresolved_total += len(unresolved)
        self._edges.replace_kinds(kinds=_VAULT_EDGE_KINDS, edges=all_edges)
        emb = self.embed_notes(notes)
        return {
            "notes": len(notes),
            "edges": len(all_edges),
            "unresolved_links": unresolved_total,
            "embedding": emb,
        }

    def embed_notes(self, notes: list[NoteRecord] | None = None) -> dict[str, Any]:
        notes = notes if notes is not None else self._vault.list_notes()
        written = 0
        skipped = 0
        model_id = self._status.model_id
        if not notes:
            return {"written": 0, "skipped_unchanged": 0, "vectors": self._vectors.count()}
        batch_size = 16
        for i in range(0, len(notes), batch_size):
            chunk = notes[i : i + batch_size]
            texts = [note_embed_text(n) for n in chunk]
            vectors = self._runtime.embed(texts)
            rows = []
            for note, text, vec in zip(chunk, texts, vectors, strict=True):
                rows.append(
                    {
                        "node_id": note.id,
                        "kind": "Note",
                        "text": text,
                        "vector": vec,
                        "model_id": model_id,
                        "meta": {
                            "name": note.title,
                            "path": note.path,
                            "kind": "Note",
                            "family": "Note",
                            "title": note.title,
                            "updated_at": note.updated_at,
                            "bucket": note.bucket,
                        },
                    }
                )
            w, s = self._vectors.upsert_many(rows)
            written += w
            skipped += s
        return {
            "written": written,
            "skipped_unchanged": skipped,
            "vectors": self._vectors.count(),
            "model": model_id,
        }

    def all_note_vectors(self) -> list[dict[str, Any]]:
        return self._vectors.all_rows()

    def notes_mentioning(self, target_id: str) -> list[str]:
        """Note ids with a mentions edge to target (symbol/file/note)."""
        out: list[str] = []
        for edge in self._edges.list_all(kind="mentions"):
            if edge.get("target_id") == target_id:
                src = str(edge.get("source_id") or "")
                if src:
                    out.append(src)
        for edge in self._edges.list_all(kind="wikilink"):
            if edge.get("target_id") == target_id:
                src = str(edge.get("source_id") or "")
                if src:
                    out.append(src)
        return list(dict.fromkeys(out))

    def notes_mentioning_name(self, name: str) -> list[str]:
        needle = name.strip().lower()
        if not needle:
            return []
        out: list[str] = []
        for edge in self._edges.list_all(kind="mentions"):
            if str(edge.get("target_name") or "").lower() == needle:
                src = str(edge.get("source_id") or "")
                if src:
                    out.append(src)
        return list(dict.fromkeys(out))

    def _index_note(self, note: NoteRecord, *, workspace_id: str | None = None) -> None:
        edges, _unresolved = self._resolve_links(note, workspace_id=workspace_id)
        self._edges.delete_by_source(note.id, kinds=_VAULT_EDGE_KINDS)
        if edges:
            self._edges.upsert_edges(edges)
        self.embed_notes([note])

    def _link_meta(self, note_id: str, body: str) -> dict[str, Any]:
        wikilinks = parse_wikilinks(body)
        outgoing = [
            e
            for e in self._edges.list_all()
            if e.get("source_id") == note_id and e.get("edge_kind") in _VAULT_EDGE_KINDS
        ]
        unresolved = [
            {
                "target": w.target,
                "raw": w.raw,
                "reason": "unresolved",
            }
            for w in wikilinks
            if not any(
                e.get("target_name", "").lower() == w.target.lower()
                or e.get("target_id", "").endswith(w.target)
                for e in outgoing
            )
        ]
        return {
            "wikilinks": [{"target": w.target, "alias": w.alias, "raw": w.raw} for w in wikilinks],
            "outgoing_edges": outgoing,
            "unresolved_links": unresolved,
        }

    def _resolve_links(
        self,
        note: NoteRecord,
        *,
        workspace_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        edges: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []
        symbols = self._load_symbols(workspace_id)

        for link in parse_wikilinks(note.body):
            target = link.target.strip()
            resolved = self._resolve_target(target, symbols)
            if resolved is None:
                unresolved.append({"target": target, "raw": link.raw, "reason": "unresolved"})
                continue
            target_id, target_kind, target_name, target_path = resolved
            if target_kind == "Note":
                edge_kind = "wikilink"
            else:
                edge_kind = "mentions"
            edge_id = f"{edge_kind}:{note.id}:{target_id}"
            edges.append(
                {
                    "id": edge_id,
                    "kind": "Edge",
                    "edge_kind": edge_kind,
                    "source_id": note.id,
                    "target_id": target_id,
                    "source_name": note.title,
                    "target_name": target_name,
                    "source_path": note.path,
                    "target_path": target_path,
                    "resolved": True,
                }
            )
        return edges, unresolved

    def _resolve_target(
        self,
        target: str,
        symbols: list[dict[str, Any]],
    ) -> tuple[str, str, str, str] | None:
        lower = target.lower()

        if lower.startswith("note:"):
            try:
                n = self._vault.get(target if target.startswith("note:") else f"note:{target}")
                return n.id, "Note", n.title, n.path
            except VaultError:
                return None

        if lower.startswith("symbol:"):
            for sym in symbols:
                if str(sym.get("id") or "").lower() == lower:
                    return (
                        str(sym["id"]),
                        "Symbol",
                        str(sym.get("name") or ""),
                        str(sym.get("path") or ""),
                    )
            return None

        if lower.startswith("file:"):
            path = target[5:]
            return f"file:{path}", "File", Path(path).name, path

        # Note by title / stem
        note = self._vault.get_by_title_or_stem(target)
        if note is not None:
            return note.id, "Note", note.title, note.path

        # Symbol by exact name (prefer unique)
        named = [s for s in symbols if str(s.get("name") or "").lower() == lower]
        if len(named) == 1:
            s = named[0]
            return str(s["id"]), "Symbol", str(s.get("name") or ""), str(s.get("path") or "")
        if len(named) > 1:
            # Prefer shortest path / first stable id
            named.sort(key=lambda s: (str(s.get("path") or ""), str(s.get("id") or "")))
            s = named[0]
            return str(s["id"]), "Symbol", str(s.get("name") or ""), str(s.get("path") or "")

        # path#symbol or path:symbol
        if "#" in target:
            path_part, name_part = target.split("#", 1)
            for s in symbols:
                if (
                    str(s.get("path") or "") == path_part
                    and str(s.get("name") or "").lower() == name_part.lower()
                ):
                    return str(s["id"]), "Symbol", str(s.get("name") or ""), str(s.get("path") or "")

        return None

    def _load_symbols(self, workspace_id: str | None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        workspaces = self._workspaces.list_workspaces()
        if workspace_id:
            workspaces = [w for w in workspaces if w.get("id") == workspace_id]
        for ws in workspaces:
            wid = str(ws.get("id") or "")
            if not wid:
                continue
            store = JsonSymbolStore(self._data_dir / "workspaces" / wid)
            rows.extend(store.list_all())
        return rows

    @staticmethod
    def _excerpt_around(body: str, needle: str, *, radius: int = 80) -> str:
        if not needle:
            return body[:160]
        idx = body.lower().find(needle.lower())
        if idx < 0:
            idx = body.lower().find(f"[[{needle.lower()}")
        if idx < 0:
            return body[:160].strip()
        start = max(0, idx - radius)
        end = min(len(body), idx + len(needle) + radius)
        chunk = body[start:end].strip()
        if start > 0:
            chunk = "…" + chunk
        if end < len(body):
            chunk = chunk + "…"
        return chunk
