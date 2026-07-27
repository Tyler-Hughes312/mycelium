"""Chat domain — thread CRUD, RAG window assembly, opt-in LLM, handoff."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mycelium.adapters.llm.openai_compatible import OpenAICompatibleLlm
from mycelium.adapters.store.thread_store import ThreadStore
from mycelium.core.config import MyceliumConfig
from mycelium.core.domain.chat_assembler import assemble_chat_prompt
from mycelium.core.domain.context_receipt import ReceiptStore, mint_receipt
from mycelium.core.domain.embedding_service import EmbeddingService
from mycelium.core.domain.impact_service import ImpactService
from mycelium.core.domain.node_types import display_kind_for_row, family_of
from mycelium.core.domain.rag_service import RagService
from mycelium.core.domain.thread_chunking import chunk_turn
from mycelium.core.domain.thread_index import index_thread_chunks
from mycelium.core.domain.vault_service import VaultService
from mycelium.core.ports.llm import LlmProvider
from mycelium.core.privacy import assert_allow_remote_llm

_DEFAULT_SYSTEM = (
    "You are Mycelium Chat. Prefer compact, retrieval-grounded answers. "
    "Cite paths and ids when helpful."
)
_HANDOFF_TOKEN_NUDGE = 8000


class ChatError(Exception):
    """Structured chat-domain failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _preview_messages(messages: list[dict[str, str]], *, max_chars: int = 120) -> list[dict[str, str]]:
    """Truncated titles/snippets only — no full prompt dump for UI."""
    out: list[dict[str, str]] = []
    for m in messages:
        role = str(m.get("role") or "")
        content = str(m.get("content") or "")
        snippet = content if len(content) <= max_chars else content[: max_chars - 1] + "…"
        out.append({"role": role, "snippet": snippet})
    return out


def _turn_seq_from_thread_chunk_id(node_id: str) -> int | None:
    """Parse turn_seq from ``node:thread_chunk:{thread_id}:{seq}:{i}``."""
    prefix = "node:thread_chunk:"
    if not node_id.startswith(prefix):
        return None
    rest = node_id[len(prefix) :]
    parts = rest.rsplit(":", 2)
    if len(parts) != 3:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def _hit_for_assembly(hit: dict[str, Any]) -> dict[str, Any]:
    """Ensure assembler sees dict meta with turn_seq (RAG packets use chip lists)."""
    out = dict(hit)
    meta = out.get("meta")
    if isinstance(meta, dict):
        if meta.get("turn_seq") is None:
            seq = _turn_seq_from_thread_chunk_id(str(out.get("id") or ""))
            if seq is not None:
                out["meta"] = {**meta, "turn_seq": seq}
        return out
    seq = _turn_seq_from_thread_chunk_id(str(out.get("id") or ""))
    out["meta"] = {"turn_seq": seq} if seq is not None else {}
    return out


def _public_assembly(assembly: dict[str, Any], *, reason: str | None = None) -> dict[str, Any]:
    messages = list(assembly.get("messages") or [])
    included_seqs = assembly.get("included_turn_seqs") or set()
    if isinstance(included_seqs, set):
        included_seqs = sorted(included_seqs)
    reason_out = reason if reason is not None else assembly.get("reason")
    return {
        "included_turn_seqs": included_seqs,
        "included_hit_ids": list(assembly.get("included_hit_ids") or []),
        "tokens_assembled": int(assembly.get("tokens_assembled") or 0),
        "tokens_full_thread_est": int(assembly.get("tokens_full_thread_est") or 0),
        "tokens_saved_est": int(assembly.get("tokens_saved_est") or 0),
        "budgets": dict(assembly.get("budgets") or {}),
        "truncated": bool(assembly.get("truncated")),
        "reason": reason_out,
        "messages_preview": _preview_messages(messages),
    }


def _resolve_api_key(cfg: MyceliumConfig) -> str:
    llm = cfg.llm
    env_name = (llm.api_key_env or "MYCELIUM_LLM_API_KEY").strip() or "MYCELIUM_LLM_API_KEY"
    key = os.environ.get(env_name, "").strip()
    if key:
        return key
    key_file = (llm.api_key_file or "").strip()
    if not key_file:
        key_file = "llm_api_key"
    path = Path(key_file).expanduser()
    if not path.is_absolute():
        path = cfg.paths.home / path
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return ""


class ChatService:
    def __init__(
        self,
        *,
        threads: ThreadStore,
        rag: RagService,
        embedding: EmbeddingService,
        vault: VaultService | None = None,
        impact: ImpactService | None = None,
        receipts: ReceiptStore | None = None,
        config: MyceliumConfig | None = None,
    ) -> None:
        self._threads = threads
        self._rag = rag
        self._embedding = embedding
        self._vault = vault
        self._impact = impact
        self._receipts = receipts
        self._config = config

    def create_thread(self, *, workspace_id: str, title: str = "") -> dict[str, Any]:
        return self._threads.create(workspace_id=workspace_id, title=title)

    def list_threads(self, *, workspace_id: str | None = None) -> list[dict[str, Any]]:
        rows = self._threads.list()
        if workspace_id is None:
            return rows
        return [r for r in rows if r.get("workspace_id") == workspace_id]

    def get_thread(
        self,
        thread_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        doc = self._threads.get(thread_id)
        if doc is None:
            raise ChatError("not_found", f"Unknown thread: {thread_id}")
        turns = list(doc.get("turns") or [])
        offset = max(0, int(offset))
        limit = max(1, min(int(limit), 500))
        page = turns[offset : offset + limit]
        return {
            **{k: v for k, v in doc.items() if k != "turns"},
            "turns": page,
            "offset": offset,
            "limit": limit,
            "turn_count": len(turns),
        }

    def search_thread(
        self,
        thread_id: str,
        query: str,
        *,
        limit: int = 8,
    ) -> dict[str, Any]:
        doc = self._threads.get(thread_id)
        if doc is None:
            raise ChatError("not_found", f"Unknown thread: {thread_id}")
        workspace_id = str(doc.get("workspace_id") or "")
        return self._rag.query_thread(
            workspace_id=workspace_id,
            thread_id=thread_id,
            query=query,
            limit=limit,
        )

    def _system_text(self) -> str:
        if self._vault is None:
            return _DEFAULT_SYSTEM
        try:
            pack = self._vault.pack(bucket="brain", max_tokens=600)
            text = str(pack.get("text") or "").strip()
            return text or _DEFAULT_SYSTEM
        except Exception:
            return _DEFAULT_SYSTEM

    def _index_turn(self, *, thread_id: str, turn: dict[str, Any], workspace_id: str) -> bool:
        """Best-effort chunk embed. Returns False when indexing failed (stale)."""
        try:
            chunks = chunk_turn(
                thread_id=thread_id,
                seq=int(turn["seq"]),
                role=str(turn.get("role") or "user"),
                text=str(turn.get("text") or ""),
            )
            index_thread_chunks(self._embedding, workspace_id, chunks)
            return True
        except Exception:
            return False

    def _resolve_llm(self, llm: LlmProvider | None) -> LlmProvider:
        if llm is not None:
            return llm
        if self._config is None:
            raise ChatError(
                "llm_not_configured",
                "No LLM configured. Enable allow_remote_llm and set an API key in Settings.",
            )
        api_key = _resolve_api_key(self._config)
        if not api_key:
            raise ChatError(
                "llm_not_configured",
                "No LLM API key found. Set MYCELIUM_LLM_API_KEY or save a key in Settings.",
            )
        assert_allow_remote_llm(self._config)
        llm_cfg = self._config.llm
        return OpenAICompatibleLlm(
            api_key=api_key,
            base_url=llm_cfg.base_url or "https://api.openai.com/v1",
            model=llm_cfg.model or "gpt-4o-mini",
        )

    def send_message(
        self,
        thread_id: str,
        text: str,
        *,
        include_code_rag: bool = True,
        llm: LlmProvider | None = None,
    ) -> dict[str, Any]:
        doc = self._threads.get(thread_id)
        if doc is None:
            raise ChatError("not_found", f"Unknown thread: {thread_id}")
        workspace_id = str(doc.get("workspace_id") or "")

        # Resolve/validate LLM before appending so missing key / privacy gate
        # cannot orphan a user turn in the thread store.
        provider = self._resolve_llm(llm)

        user_turn = self._threads.append_turn(thread_id, role="user", text=text)
        index_ok = self._index_turn(
            thread_id=thread_id, turn=user_turn, workspace_id=workspace_id
        )
        index_stale = not index_ok
        reason: str | None = "index_stale" if index_stale else None

        system_text = self._system_text()

        thread_hits: list[dict[str, Any]] = []
        if not index_stale:
            try:
                thread_packet = self._rag.query_thread(
                    workspace_id=workspace_id,
                    thread_id=thread_id,
                    query=text,
                    limit=8,
                )
                thread_hits = list(thread_packet.get("results") or [])
            except Exception:
                thread_hits = []
                reason = "index_stale"
                index_stale = True
        else:
            thread_hits = []

        code_hits: list[dict[str, Any]] = []
        if include_code_rag:
            try:
                code_packet = self._rag.query(
                    workspace_id=workspace_id,
                    query=text,
                    limit=6,
                )
                for row in code_packet.get("results") or []:
                    # Exclude Thread family (ThreadChunk) from code RAG path —
                    # catch lowercase / meta-only kinds via display_kind_for_row.
                    if family_of(display_kind_for_row(row)) == "Thread":
                        continue
                    code_hits.append(row)
            except Exception:
                code_hits = []

        all_turns = self._threads.list_turns(thread_id)
        assembly = assemble_chat_prompt(
            system_text=system_text,
            all_turns=all_turns,
            query_text=text,
            thread_hits=[_hit_for_assembly(h) for h in thread_hits],
            code_hits=[_hit_for_assembly(h) for h in code_hits],
        )
        if reason:
            assembly = {**assembly, "reason": reason}

        reply = provider.complete(list(assembly.get("messages") or []))

        assistant_turn = self._threads.append_turn(
            thread_id, role="assistant", text=reply
        )
        if not self._index_turn(
            thread_id=thread_id, turn=assistant_turn, workspace_id=workspace_id
        ):
            reason = reason or "index_stale"
            assembly = {**assembly, "reason": reason}

        rag_results = list(thread_hits) + list(code_hits)
        receipt = mint_receipt(
            tool="chat",
            workspace_id=workspace_id,
            head="",
            results=rag_results,
            query=text,
            served_tokens=int(assembly.get("tokens_assembled") or 0),
        )
        if self._receipts is not None:
            public = self._receipts.put(receipt)
        else:
            public = {
                "id": receipt["id"],
                "head": receipt.get("head"),
                "item_count": receipt.get("item_count"),
                "served_tokens": receipt.get("served_tokens"),
                "tool": receipt.get("tool"),
                "workspace_id": receipt.get("workspace_id"),
            }
        # Keep attestation items for Context used UI
        public = {**public, "items": receipt.get("items") or []}

        self._threads.set_fields(
            thread_id,
            last_receipt_id=str(receipt.get("id") or ""),
            last_receipt_items=list(receipt.get("items") or []),
        )

        if self._impact is not None:
            self._impact.record_chat_turn(
                served=int(assembly.get("tokens_assembled") or 0),
                baseline=int(assembly.get("tokens_full_thread_est") or 0),
                workspace_id=workspace_id,
                receipt_id=str(receipt.get("id") or "") or None,
            )

        nudge_handoff = (
            int(assembly.get("tokens_full_thread_est") or 0) > _HANDOFF_TOKEN_NUDGE
            or bool(assembly.get("truncated"))
        )

        return {
            "assistant": assistant_turn,
            "receipt": public,
            "assembly": _public_assembly(assembly, reason=reason),
            "nudge_handoff": nudge_handoff,
        }

    def handoff(self, thread_id: str, *, summary: str | None = None) -> dict[str, Any]:
        doc = self._threads.get(thread_id)
        if doc is None:
            raise ChatError("not_found", f"Unknown thread: {thread_id}")
        if self._vault is None:
            raise ChatError("vault_unavailable", "Thinking Vault is not configured.")

        turns = list(doc.get("turns") or [])
        last_user = next(
            (t for t in reversed(turns) if t.get("role") == "user"),
            None,
        )
        intent = ""
        if summary and summary.strip():
            intent = summary.strip()
        elif last_user is not None:
            # Curated: short intent only — never paste full turn text dump
            raw = str(last_user.get("text") or "").strip()
            intent = raw[:240] + ("…" if len(raw) > 240 else "")

        items = list(doc.get("last_receipt_items") or [])
        receipt_id = str(doc.get("last_receipt_id") or "")
        bullets: list[str] = []
        if receipt_id:
            bullets.append(f"- Receipt: `{receipt_id}`")
        for item in items[:12]:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or "")
            title = str(item.get("title") or "")
            rid = str(item.get("id") or "")
            label = title or path or rid
            if path and title:
                bullets.append(f"- [{title}]({path}) `{rid}`".rstrip())
            elif label:
                bullets.append(f"- {label}" + (f" `{rid}`" if rid else ""))

        title = f"Chat handoff — {str(doc.get('title') or thread_id)[:60]}"
        body_parts = [
            f"# {title}",
            "",
            "## Intent",
            "",
            intent or "(no user intent captured)",
            "",
            "## Context cited",
            "",
        ]
        if bullets:
            body_parts.extend(bullets)
        else:
            body_parts.append("- (no receipt items yet)")
        body_parts.extend(
            [
                "",
                "## Open questions",
                "",
                "- ",
                "",
            ]
        )
        body = "\n".join(body_parts)

        note = self._vault.create_note(title=title, body=body, bucket="work/active")
        handoff_path = str(note.get("path") or "")
        self._threads.set_fields(thread_id, handoff_path=handoff_path)
        return {
            "note": note,
            "handoff_path": handoff_path,
            "path": handoff_path,
        }
