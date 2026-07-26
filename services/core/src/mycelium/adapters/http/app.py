"""HTTP adapter — FastAPI surface for Desktop / Editor / MCP clients."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from mycelium import __version__
from mycelium.adapters.embeddings.bootstrap import bootstrap_embedder, status_dict
from mycelium.adapters.git import GitError
from mycelium.adapters.git.watcher import WorkspaceWatcherManager
from mycelium.adapters.store import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.config import MyceliumConfig, ensure_local_layout
from mycelium.core.domain.index_service import IndexService
from mycelium.core.domain.rag_service import RagService

# Default bind for docs / run helpers (AD-2). Actual uvicorn host should be 127.0.0.1.
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


class QueryRequest(BaseModel):
    query: str
    workspace_id: str = Field(..., min_length=1)
    limit: int = Field(default=8, ge=1, le=10)


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


def _http_error(exc: WorkspaceError | GitError) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={"code": exc.code, "message": exc.message},
    )


def create_app(config: MyceliumConfig | None = None) -> FastAPI:
    """Build FastAPI app; ensures local config/data dirs on startup."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        cfg = config or ensure_local_layout()
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
        watchers = WorkspaceWatcherManager(index)
        watchers.start_all(repo.list_workspaces())
        application.state.mycelium_config = cfg
        application.state.workspace_repo = repo
        application.state.index_service = index
        application.state.rag_service = rag
        application.state.embedding_status = emb_status
        application.state.watchers = watchers
        try:
            yield
        finally:
            watchers.stop_all()

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
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def workspace_repo() -> JsonFileWorkspaceRepo:
        return application.state.workspace_repo

    def index_service() -> IndexService:
        return application.state.index_service

    def rag_service() -> RagService:
        return application.state.rag_service

    def watchers() -> WorkspaceWatcherManager:
        return application.state.watchers

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
            payload["privacy"] = {
                "allow_code_upload": cfg.network.allow_code_upload,
                "allow_remote_llm": cfg.network.allow_remote_llm,
            }
            payload["paths"] = {
                "config": str(cfg.paths.config_file),
                "data": str(cfg.paths.data_dir),
            }
            payload["index"] = {"history_depth": cfg.index.history_depth}
            payload["embedding"] = {
                "configured_model": cfg.embedding.model,
                **(status_dict(emb) if emb is not None else {}),
            }
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
    def query(body: QueryRequest) -> dict[str, Any]:
        try:
            return rag_service().query(
                workspace_id=body.workspace_id,
                query=body.query,
                limit=body.limit,
            )
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc

    @application.post("/context/focus")
    def context_focus(body: FocusRequest) -> dict[str, Any]:
        try:
            return rag_service().focus(
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

    return application


# Module-level app for `uvicorn mycelium.adapters.http.app:app` / `main:app`
app = create_app()
