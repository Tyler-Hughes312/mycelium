"""HTTP adapter — FastAPI surface for Desktop / Editor / MCP clients."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mycelium import __version__
from mycelium.adapters.embeddings.bootstrap import bootstrap_embedder, status_dict
from mycelium.adapters.git import GitError
from mycelium.adapters.git.watcher import VaultWatcher, WorkspaceWatcherManager
from mycelium.adapters.github import GitHubError, GitHubService
from mycelium.adapters.llm.echo import EchoLlm
from mycelium.adapters.store import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.adapters.store.impact_store import ImpactStore
from mycelium.adapters.store.thread_store import ThreadStore
from mycelium.adapters.vault import VaultError
from mycelium.adapters.git.files import git_head
from mycelium.core.config import (
    MyceliumConfig,
    ensure_local_layout,
    settings_dict,
    update_config,
)
from mycelium.core.domain.chat_service import ChatError, ChatService
from mycelium.core.domain.context_receipt import ReceiptStore, mint_receipt
from mycelium.core.domain.impact_pricing import pricing_table
from mycelium.core.domain.impact_service import ImpactService
from mycelium.core.domain.index_service import IndexService
from mycelium.core.domain.rag_service import RagService
from mycelium.core.domain.vault_service import VaultService, estimate_tokens
from mycelium.core.logging import setup_logging
from mycelium.core.ports.llm import LlmProvider
from mycelium.core.privacy import PrivacyError

log = logging.getLogger("mycelium.http")

# Default bind for docs / run helpers (AD-2). Actual uvicorn host should be 127.0.0.1.
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


class QueryRequest(BaseModel):
    query: str
    # Use "*" or "all" to search every registered workspace (reuse old code across repos).
    workspace_id: str = Field(default="*", min_length=1)
    limit: int = Field(default=8, ge=1, le=10)
    kinds: list[str] | None = None


class FocusRequest(BaseModel):
    workspace_id: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    symbol: str | None = None
    line: int | None = None
    limit: int = Field(default=10, ge=1, le=10)


class RegisterWorkspaceRequest(BaseModel):
    path: str = Field(..., min_length=1)


class FileChangedHookRequest(BaseModel):
    path: str = Field(..., min_length=1)


class CreateNoteRequest(BaseModel):
    title: str = Field(..., min_length=1)
    body: str = ""
    filename: str | None = None
    link_symbol: str | None = None
    bucket: str | None = None


class UpdateNoteRequest(BaseModel):
    title: str | None = None
    body: str | None = None


class CreateBucketRequest(BaseModel):
    name: str = Field(..., min_length=1)


class PackVaultRequest(BaseModel):
    bucket: str | None = None
    max_tokens: int = Field(default=2000, ge=64, le=100_000)
    include_bodies: bool = True


class PatchSettingsRequest(BaseModel):
    vault_dir: str | None = None
    history_depth: int | None = Field(default=None, ge=1, le=50_000)
    embedding_model: str | None = None
    allow_code_upload: bool | None = None
    allow_remote_llm: bool | None = None
    github_client_id: str | None = None
    impact_tracking_enabled: bool | None = None
    impact_default_model: str | None = None
    impact_pricing_overrides: dict[str, float] | None = None


class GitHubPatRequest(BaseModel):
    token: str = Field(..., min_length=1)


class GitHubImportRequest(BaseModel):
    clone_url: str = Field(..., min_length=1)
    dest: str | None = None
    full_name: str | None = None


class CreateThreadRequest(BaseModel):
    workspace_id: str = Field(..., min_length=1)
    title: str = ""


class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1)
    include_code_rag: bool = True


class SearchThreadRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=8, ge=1, le=50)


class HandoffRequest(BaseModel):
    summary: str | None = None


def _http_error(exc: WorkspaceError | GitError | VaultError | GitHubError) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={"code": exc.code, "message": exc.message},
    )


def _impact_probe(request: Request) -> dict[str, Any] | None:
    model_id = (request.headers.get("X-Mycelium-Model-Id") or "").strip()
    if not model_id:
        return None
    probe: dict[str, Any] = {"model_id": model_id}
    probe_key = (request.headers.get("X-Mycelium-Model-Probe") or "").strip()
    if probe_key:
        probe[probe_key] = model_id
    return probe


def create_app(config: MyceliumConfig | None = None) -> FastAPI:
    """Build FastAPI app; ensures local config/data dirs on startup."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        cfg = config or ensure_local_layout()
        setup_logging(cfg.paths.home / "logs")
        repo = JsonFileWorkspaceRepo(cfg.paths.data_dir)
        runtime, emb_status = bootstrap_embedder(
            model=cfg.embedding.model,
            cache_dir=cfg.paths.home / "models",
        )
        index = IndexService(
            data_dir=cfg.paths.data_dir,
            workspace_repo=repo,
            history_depth=cfg.index.history_depth,
            embedding_runtime=runtime,
            embedding_status=emb_status,
            embedding_model=cfg.embedding.model,
        )
        rag = RagService(
            data_dir=cfg.paths.data_dir,
            workspace_repo=repo,
            runtime=runtime,
            status=emb_status,
            model=cfg.embedding.model,
        )
        vault = VaultService(
            vault_dir=cfg.paths.vault_dir,
            data_dir=cfg.paths.data_dir,
            workspace_repo=repo,
            runtime=runtime,
            status=emb_status,
            model=cfg.embedding.model,
        )
        rag.attach_vault(vault)
        watchers = WorkspaceWatcherManager(index)
        watchers.start_all(repo.list_workspaces())
        vault_watcher = VaultWatcher(vault)
        vault_watcher.start(cfg.paths.vault_dir)
        application.state.mycelium_config = cfg
        application.state.workspace_repo = repo
        application.state.index_service = index
        application.state.rag_service = rag
        application.state.vault_service = vault
        application.state.embedding_status = emb_status
        application.state.watchers = watchers
        application.state.vault_watcher = vault_watcher
        application.state.github = GitHubService(
            home=cfg.paths.home,
            client_id=cfg.github.client_id,
        )
        impact = ImpactService(
            ImpactStore(cfg.paths.data_dir / "impact_events.json"),
            enabled=cfg.impact.tracking_enabled,
            default_model=cfg.impact.default_model,
            pricing_overrides=cfg.impact.pricing_overrides,
        )
        # Older Desktop sidecars logged tokens without $ — fill on upgrade.
        from mycelium.core.domain.impact_pricing import rate_for_model

        impact.store.backfill_pricing(
            default_model=cfg.impact.default_model,
            usd_per_1m_input=rate_for_model(
                cfg.impact.default_model, cfg.impact.pricing_overrides
            ),
        )
        application.state.impact_service = impact
        receipt_store = ReceiptStore(cfg.paths.data_dir / "context_receipts.json")
        application.state.receipt_store = receipt_store
        thread_store = ThreadStore(cfg.paths.data_dir / "threads")
        application.state.thread_store = thread_store
        application.state.chat_service = ChatService(
            threads=thread_store,
            rag=rag,
            embedding=index.embedding_service,
            vault=vault,
            impact=impact,
            receipts=receipt_store,
            config=cfg,
        )
        # Tests/dev: MYCELIUM_LLM=echo or app.state.chat_llm override (no API key).
        if os.environ.get("MYCELIUM_LLM", "").strip().lower() == "echo":
            application.state.chat_llm = EchoLlm()
        else:
            application.state.chat_llm = None
        try:
            yield
        finally:
            watchers.stop_all()
            vault_watcher.stop()

    application = FastAPI(
        title="Mycelium Core",
        version=__version__,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            # Tauri 2 webview origins (packaged Desktop)
            "tauri://localhost",
            "https://tauri.localhost",
            "http://tauri.localhost",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def api_token_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        cfg: MyceliumConfig | None = getattr(application.state, "mycelium_config", None)
        expected = (cfg.server.api_token if cfg else "") or ""
        if not expected:
            return await call_next(request)
        # Keep /health reachable for local ops without a token.
        if request.url.path == "/health":
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        if auth == f"Bearer {expected}":
            return await call_next(request)
        return JSONResponse(
            status_code=401,
            content={
                "detail": {
                    "code": "unauthorized",
                    "message": "Invalid or missing API token",
                }
            },
        )

    @application.exception_handler(PrivacyError)
    async def privacy_error_handler(_request: Request, exc: PrivacyError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @application.exception_handler(ChatError)
    async def chat_error_handler(_request: Request, exc: ChatError) -> JSONResponse:
        status = 404 if exc.code == "not_found" else 400
        return JSONResponse(
            status_code=status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @application.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, HTTPException):
            raise exc
        log.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "code": "internal_error",
                    "message": "Internal server error",
                }
            },
        )

    def workspace_repo() -> JsonFileWorkspaceRepo:
        return application.state.workspace_repo

    def index_service() -> IndexService:
        return application.state.index_service

    def rag_service() -> RagService:
        return application.state.rag_service

    def vault_service() -> VaultService:
        return application.state.vault_service

    def github() -> GitHubService:
        return application.state.github

    def impact_service() -> ImpactService:
        return application.state.impact_service

    def receipt_store() -> ReceiptStore:
        return application.state.receipt_store

    def chat_service() -> ChatService:
        return application.state.chat_service

    def _resolve_chat_llm() -> LlmProvider | None:
        override = getattr(application.state, "chat_llm", None)
        if override is not None:
            return override
        if os.environ.get("MYCELIUM_LLM", "").strip().lower() == "echo":
            return EchoLlm()
        return None

    def watchers() -> WorkspaceWatcherManager:
        return application.state.watchers

    def _workspace_root(workspace_id: str | None) -> Path | None:
        if not workspace_id or workspace_id in ("*", "all"):
            return None
        row = workspace_repo().get(workspace_id)
        if not row:
            return None
        raw = str(row.get("path") or "")
        if not raw:
            return None
        return Path(raw)

    def _workspace_head(workspace_id: str | None) -> str:
        root = _workspace_root(workspace_id)
        if root is None:
            return ""
        return git_head(root) or ""

    def _attach_receipt(
        *,
        tool: str,
        payload: dict[str, Any],
        query: str = "",
        served_tokens: int = 0,
    ) -> dict[str, Any]:
        """Mint compact receipt (ids/paths only) and attach public slice to payload."""
        wid = str(payload.get("workspace_id") or "")
        results = list(payload.get("results") or [])
        if tool == "vault_pack":
            # Pack has no RAG results — receipt cites pack meta only
            results = [
                {
                    "id": f"pack:{payload.get('bucket') or 'vault'}",
                    "path": str(payload.get("bucket") or "vault"),
                    "kind": "Pack",
                    "title": f"vault pack ≤{payload.get('max_tokens', '')}",
                }
            ]
        receipt = mint_receipt(
            tool=tool,
            workspace_id=wid if wid not in ("*", "all") else "",
            head=_workspace_head(wid if wid not in ("*", "all") else None),
            results=results,
            query=query,
            served_tokens=served_tokens,
        )
        public = receipt_store().put(receipt)
        payload["receipt"] = public
        return receipt

    @application.get("/health")
    def health() -> dict[str, Any]:
        cfg: MyceliumConfig | None = getattr(application.state, "mycelium_config", None)
        emb = getattr(application.state, "embedding_status", None)
        payload: dict[str, Any] = {
            "status": "ok",
            "service": "mycelium-core",
            "version": __version__,
            "bind": {
                "host": (cfg.server.host if cfg else DEFAULT_HOST),
                "port": (cfg.server.port if cfg else DEFAULT_PORT),
            },
        }
        if cfg is not None:
            payload["config_version"] = cfg.config_version
            payload["privacy"] = {
                "allow_code_upload": cfg.network.allow_code_upload,
                "allow_remote_llm": cfg.network.allow_remote_llm,
            }
            payload["paths"] = {
                "config": str(cfg.paths.config_file),
                "data": str(cfg.paths.data_dir),
                "vault": str(cfg.paths.vault_dir),
            }
            payload["index"] = {"history_depth": cfg.index.history_depth}
            payload["embedding"] = {
                "configured_model": cfg.embedding.model,
                **(status_dict(emb) if emb is not None else {}),
            }
            payload["api_token_enabled"] = bool(cfg.server.api_token)
        watchers_state = getattr(application.state, "watchers", None)
        if watchers_state is not None and hasattr(watchers_state, "status"):
            payload["watchers"] = watchers_state.status()
        return payload

    @application.get("/embeddings/status")
    def embeddings_status() -> dict[str, Any]:
        cfg: MyceliumConfig = application.state.mycelium_config
        emb = application.state.embedding_status
        return {
            "configured_model": cfg.embedding.model,
            **status_dict(emb),
        }

    @application.post("/workspaces/{workspace_id}/embeddings")
    def embed_workspace(workspace_id: str) -> dict[str, Any]:
        try:
            stats = index_service().embedding_service.embed_workspace(workspace_id)
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        return {"embedding": stats}

    @application.get("/workspaces")
    def list_workspaces() -> dict[str, Any]:
        return {"workspaces": workspace_repo().list_workspaces()}

    @application.post("/workspaces", status_code=201)
    def register_workspace(body: RegisterWorkspaceRequest) -> dict[str, Any]:
        try:
            row = workspace_repo().register(body.path)
        except WorkspaceError as exc:
            raise _http_error(exc) from exc
        watchers().start(row["id"], row["path"])
        return {"workspace": row}

    @application.post("/workspaces/{workspace_id}/index")
    def start_index(workspace_id: str) -> dict[str, Any]:
        try:
            status = index_service().start_index_async(workspace_id)
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        return {"status": status, "accepted": True}

    @application.post("/workspaces/{workspace_id}/index/cancel")
    def cancel_index(workspace_id: str) -> dict[str, Any]:
        if workspace_repo().get(workspace_id) is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": f"Unknown workspace id: {workspace_id}"},
            )
        status = index_service().request_cancel(workspace_id)
        return {"status": status}

    @application.get("/workspaces/{workspace_id}/index/status")
    def index_status(workspace_id: str) -> dict[str, Any]:
        if workspace_repo().get(workspace_id) is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": f"Unknown workspace id: {workspace_id}"},
            )
        status = index_service().get_status(workspace_id)
        return {
            "status": status
            or {
                "workspace_id": workspace_id,
                "status": "idle",
                "progress": 0,
                "message": "No index run yet",
                "cancellable": False,
            }
        }

    @application.post("/workspaces/{workspace_id}/sync")
    def sync_workspace(workspace_id: str) -> dict[str, Any]:
        """Auto-index dirty files / start full index if HEAD moved (MCP freshness)."""
        if workspace_repo().get(workspace_id) is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": f"Unknown workspace id: {workspace_id}"},
            )
        try:
            return {"sync": index_service().sync_pending_changes(workspace_id)}
        except WorkspaceError as exc:
            raise _http_error(exc) from exc

    @application.get("/workspaces/{workspace_id}/commits")
    def list_commits(workspace_id: str, limit: int = 50) -> dict[str, Any]:
        try:
            rows = index_service().list_commits(workspace_id, limit=min(max(limit, 1), 500))
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        return {"commits": rows, "count": len(rows)}

    @application.get("/workspaces/{workspace_id}/symbols")
    def list_symbols(workspace_id: str, limit: int = 100) -> dict[str, Any]:
        try:
            rows = index_service().list_symbols(workspace_id, limit=min(max(limit, 1), 1000))
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        return {"symbols": rows, "count": len(rows)}

    @application.get("/workspaces/{workspace_id}/edges")
    def list_edges(
        workspace_id: str,
        kind: str | None = "co_changed",
        limit: int = 100,
    ) -> dict[str, Any]:
        try:
            rows = index_service().list_edges(
                workspace_id,
                kind=kind,
                limit=min(max(limit, 1), 1000),
            )
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        return {"edges": rows, "count": len(rows)}

    @application.post("/workspaces/{workspace_id}/hooks/file-changed")
    def file_changed_hook(
        workspace_id: str,
        body: FileChangedHookRequest,
    ) -> dict[str, Any]:
        """Editor/FS hook: incrementally reindex one file (FR-4)."""
        try:
            result = index_service().reindex_file(workspace_id, body.path)
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        return {"update": result}

    @application.post("/query")
    def query(body: QueryRequest, request: Request) -> dict[str, Any]:
        try:
            result = rag_service().query(
                workspace_id=body.workspace_id,
                query=body.query,
                limit=body.limit,
                kinds=body.kinds,
            )
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        snippets = [
            str(r.get("snippet") or "")
            for r in (result.get("results") or [])
            if isinstance(r, dict)
        ]
        served = estimate_tokens("\n".join(snippets)) if snippets else 0
        receipt = _attach_receipt(
            tool="search",
            payload=result,
            query=body.query,
            served_tokens=served,
        )
        impact_service().record_search_or_focus(
            tool="search",
            payload=result,
            workspace_root=_workspace_root(
                body.workspace_id if body.workspace_id not in ("*", "all") else None
            ),
            probe=_impact_probe(request),
            receipt_id=str(receipt.get("id") or ""),
        )
        return result

    @application.post("/context/focus")
    def context_focus(body: FocusRequest, request: Request) -> dict[str, Any]:
        try:
            result = rag_service().focus(
                workspace_id=body.workspace_id,
                path=body.path,
                symbol=body.symbol,
                line=body.line,
                limit=body.limit,
            )
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        snippets = [
            str(r.get("snippet") or "")
            for r in (result.get("results") or [])
            if isinstance(r, dict)
        ]
        served = estimate_tokens("\n".join(snippets)) if snippets else 0
        receipt = _attach_receipt(
            tool="focus",
            payload=result,
            query=f"{body.path}#{body.symbol or ''}",
            served_tokens=served,
        )
        impact_service().record_search_or_focus(
            tool="focus",
            payload=result,
            workspace_root=_workspace_root(body.workspace_id),
            probe=_impact_probe(request),
            receipt_id=str(receipt.get("id") or ""),
        )
        return result

    @application.get("/vault")
    def vault_info() -> dict[str, Any]:
        return {"vault": vault_service().info()}

    @application.get("/vault/tree")
    def vault_tree() -> dict[str, Any]:
        return vault_service().list_tree()

    @application.post("/vault/buckets", status_code=201)
    def create_bucket(body: CreateBucketRequest) -> dict[str, Any]:
        try:
            return {"bucket": vault_service().create_bucket(body.name)}
        except VaultError as exc:
            raise _http_error(exc) from exc

    @application.post("/vault/scaffold")
    def vault_scaffold() -> dict[str, Any]:
        """Ensure kepano / obsidian-mind inspired folder layout (idempotent)."""
        return {"scaffold": vault_service().ensure_scaffold()}

    @application.post("/vault/pack")
    def vault_pack(body: PackVaultRequest, request: Request) -> dict[str, Any]:
        try:
            pack = vault_service().pack(
                bucket=body.bucket,
                max_tokens=body.max_tokens,
                include_bodies=body.include_bodies,
            )
        except VaultError as exc:
            raise _http_error(exc) from exc
        pack_payload = {
            "workspace_id": "",
            "results": [],
            "bucket": body.bucket,
            "max_tokens": body.max_tokens,
            "tokens_est": pack.get("tokens_est"),
        }
        receipt = _attach_receipt(
            tool="vault_pack",
            payload=pack_payload,
            query=str(body.bucket or "vault"),
            served_tokens=int(pack.get("tokens_est") or 0),
        )
        pack["receipt"] = pack_payload.get("receipt")
        impact_service().record_pack(
            pack=pack,
            max_tokens=body.max_tokens,
            probe=_impact_probe(request),
            receipt_id=str(receipt.get("id") or ""),
        )
        return {"pack": pack}

    @application.get("/context/receipts/{receipt_id}")
    def get_receipt(receipt_id: str) -> dict[str, Any]:
        row = receipt_store().get(receipt_id)
        if not row:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": f"Unknown receipt: {receipt_id}"},
            )
        current = _workspace_head(str(row.get("workspace_id") or "") or None)
        stored = str(row.get("head") or "")
        status = "valid" if stored and stored == current else ("stale" if stored else "unknown")
        # Return compact verify payload — no snippet/bodies
        return {
            "receipt": {
                "id": row.get("id"),
                "status": status,
                "tool": row.get("tool"),
                "workspace_id": row.get("workspace_id"),
                "head": stored,
                "head_now": current,
                "item_count": row.get("item_count"),
                "served_tokens": row.get("served_tokens"),
                "items": row.get("items") or [],
            }
        }

    @application.get("/vault/notes")
    def list_notes() -> dict[str, Any]:
        notes = vault_service().list_notes()
        return {"notes": notes, "count": len(notes)}

    @application.post("/vault/notes", status_code=201)
    def create_note(body: CreateNoteRequest) -> dict[str, Any]:
        try:
            note = vault_service().create_note(
                title=body.title,
                body=body.body,
                filename=body.filename,
                link_symbol=body.link_symbol,
                bucket=body.bucket,
            )
        except VaultError as exc:
            raise _http_error(exc) from exc
        return {"note": note}

    def _nid(note_id: str) -> str:
        return note_id if note_id.startswith("note:") else f"note:{note_id}"

    @application.get("/vault/notes/{note_id:path}/backlinks")
    def note_backlinks(note_id: str) -> dict[str, Any]:
        try:
            return vault_service().backlinks(_nid(note_id))
        except VaultError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc

    @application.get("/vault/notes/{note_id:path}")
    def get_note(note_id: str) -> dict[str, Any]:
        try:
            note = vault_service().get_note(_nid(note_id))
        except VaultError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        return {"note": note}

    @application.put("/vault/notes/{note_id:path}")
    def update_note(note_id: str, body: UpdateNoteRequest) -> dict[str, Any]:
        try:
            note = vault_service().update_note(
                _nid(note_id), title=body.title, body=body.body
            )
        except VaultError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        return {"note": note}

    @application.delete("/vault/notes/{note_id:path}")
    def delete_note(note_id: str) -> dict[str, Any]:
        nid = _nid(note_id)
        try:
            vault_service().delete_note(nid)
        except VaultError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        return {"deleted": True, "id": nid}

    @application.post("/vault/reindex")
    def vault_reindex(workspace_id: str | None = None) -> dict[str, Any]:
        return {"reindex": vault_service().reindex(workspace_id=workspace_id)}

    @application.get("/impact/summary")
    def impact_summary(range: str = "all") -> dict[str, Any]:
        range_name = range if range in ("today", "week", "all") else "all"
        return {"summary": impact_service().store.summary(range_name)}  # type: ignore[arg-type]

    @application.get("/impact/pricing")
    def impact_pricing() -> dict[str, Any]:
        svc = impact_service()
        return pricing_table(
            default_model=svc.default_model,
            overrides=svc.pricing_overrides,
        )

    @application.get("/impact/events")
    def impact_events(limit: int = 50) -> dict[str, Any]:
        events = impact_service().store.list_events(limit)
        return {"events": events, "count": len(events)}

    @application.delete("/impact/events")
    def impact_clear() -> dict[str, Any]:
        impact_service().store.clear()
        return {"cleared": True}

    @application.post("/threads", status_code=201)
    def create_thread(body: CreateThreadRequest) -> dict[str, Any]:
        thread = chat_service().create_thread(
            workspace_id=body.workspace_id,
            title=body.title or "",
        )
        return {"thread": thread}

    @application.get("/threads")
    def list_threads(workspace_id: str | None = None) -> dict[str, Any]:
        rows = chat_service().list_threads(workspace_id=workspace_id)
        return {"threads": rows, "count": len(rows)}

    @application.get("/threads/{thread_id}")
    def get_thread(
        thread_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        return chat_service().get_thread(thread_id, offset=offset, limit=limit)

    @application.post("/threads/{thread_id}/messages")
    def send_thread_message(
        thread_id: str,
        body: SendMessageRequest,
    ) -> dict[str, Any]:
        return chat_service().send_message(
            thread_id,
            body.text,
            include_code_rag=body.include_code_rag,
            llm=_resolve_chat_llm(),
        )

    @application.post("/threads/{thread_id}/search")
    def search_thread(thread_id: str, body: SearchThreadRequest) -> dict[str, Any]:
        return chat_service().search_thread(
            thread_id,
            body.query,
            limit=body.limit,
        )

    @application.post("/threads/{thread_id}/handoff")
    def handoff_thread(
        thread_id: str,
        body: HandoffRequest = HandoffRequest(),
    ) -> dict[str, Any]:
        return chat_service().handoff(thread_id, summary=body.summary)

    @application.get("/settings")
    def get_settings() -> dict[str, Any]:
        cfg: MyceliumConfig = application.state.mycelium_config
        emb = application.state.embedding_status
        return {
            "settings": settings_dict(cfg),
            "embedding_runtime": status_dict(emb) if emb is not None else {},
            "github": github().status(),
        }

    @application.patch("/settings")
    def patch_settings(body: PatchSettingsRequest) -> dict[str, Any]:
        cfg: MyceliumConfig = application.state.mycelium_config
        updated = update_config(
            cfg.paths.home,
            vault_dir=body.vault_dir,
            history_depth=body.history_depth,
            embedding_model=body.embedding_model,
            allow_code_upload=body.allow_code_upload,
            allow_remote_llm=body.allow_remote_llm,
            github_client_id=body.github_client_id,
            impact_tracking_enabled=body.impact_tracking_enabled,
            impact_default_model=body.impact_default_model,
            impact_pricing_overrides=body.impact_pricing_overrides,
        )
        application.state.mycelium_config = updated
        application.state.github = GitHubService(
            home=updated.paths.home,
            client_id=updated.github.client_id,
        )
        impact_service().set_enabled(updated.impact.tracking_enabled)
        impact_service().set_pricing(
            default_model=updated.impact.default_model,
            pricing_overrides=updated.impact.pricing_overrides,
        )
        # Hot-swap vault + index depth; embedding model change needs Core restart
        runtime = application.state.index_service.embedding_service.runtime
        emb_status = application.state.embedding_status
        vault = VaultService(
            vault_dir=updated.paths.vault_dir,
            data_dir=updated.paths.data_dir,
            workspace_repo=application.state.workspace_repo,
            runtime=runtime,
            status=emb_status,
            model=updated.embedding.model,
        )
        application.state.vault_service = vault
        application.state.rag_service.attach_vault(vault)
        application.state.chat_service = ChatService(
            threads=application.state.thread_store,
            rag=application.state.rag_service,
            embedding=application.state.index_service.embedding_service,
            vault=vault,
            impact=impact_service(),
            receipts=receipt_store(),
            config=updated,
        )
        application.state.index_service.history_depth = updated.index.history_depth
        restart_hint = None
        if (
            body.embedding_model is not None
            and body.embedding_model.strip() != cfg.embedding.model
        ):
            restart_hint = (
                "Embedding model updated in config. Restart Core to load the new model."
            )
        return {
            "settings": settings_dict(updated),
            "github": github().status(),
            "restart_hint": restart_hint,
        }

    @application.get("/integrations/github/status")
    def github_status() -> dict[str, Any]:
        return github().status()

    @application.post("/integrations/github/device/start")
    def github_device_start() -> dict[str, Any]:
        try:
            return github().device_start()
        except GitHubError as exc:
            raise _http_error(exc) from exc

    @application.post("/integrations/github/device/poll")
    def github_device_poll() -> dict[str, Any]:
        try:
            return github().device_poll()
        except GitHubError as exc:
            raise _http_error(exc) from exc

    @application.post("/integrations/github/token")
    def github_save_pat(body: GitHubPatRequest) -> dict[str, Any]:
        try:
            return github().save_pat(body.token)
        except GitHubError as exc:
            if exc.code == "unauthorized":
                raise HTTPException(
                    status_code=401,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc

    @application.delete("/integrations/github")
    def github_disconnect() -> dict[str, Any]:
        return github().disconnect()

    @application.get("/integrations/github/repos")
    def github_repos(page: int = 1, per_page: int = 30) -> dict[str, Any]:
        try:
            return github().list_repos(page=page, per_page=per_page)
        except GitHubError as exc:
            if exc.code in {"not_connected", "unauthorized"}:
                raise HTTPException(
                    status_code=401,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc

    @application.post("/integrations/github/import")
    def github_import(body: GitHubImportRequest) -> dict[str, Any]:
        try:
            result = github().import_repo(
                clone_url=body.clone_url,
                dest=body.dest,
                full_name=body.full_name,
                workspace_repo=workspace_repo(),
            )
        except GitHubError as exc:
            if exc.code == "not_connected":
                raise HTTPException(
                    status_code=401,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        except WorkspaceError as exc:
            raise _http_error(exc) from exc
        row = result["workspace"]
        watchers().start(row["id"], row["path"])
        return result

    return application


# Module-level app for `uvicorn mycelium.adapters.http.app:app` / `main:app`
app = create_app()
