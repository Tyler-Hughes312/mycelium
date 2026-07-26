"""HTTP adapter — FastAPI surface for Desktop / Editor / MCP clients."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from mycelium import __version__
from mycelium.adapters.git import GitError
from mycelium.adapters.store import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.config import MyceliumConfig, ensure_local_layout
from mycelium.core.domain.index_service import IndexService

# Default bind for docs / run helpers (AD-2). Actual uvicorn host should be 127.0.0.1.
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787

MOCK_RESULTS: list[dict[str, Any]] = [
    {
        "title": "rateLimitMiddleware Implementation",
        "kind": "Symbol",
        "snippet": "export const rateLimitMiddleware = (req, res, next) => { ... // handles 429 backoff",
        "path": "src/api/middleware.ts",
        "meta": [
            {"icon": "folder", "text": "src/api/middleware.ts"},
            {"icon": "schedule", "text": "2d ago"},
        ],
        "score": 0.94,
    },
    {
        "title": "Update Redis ratelimit configuration",
        "kind": "Commit",
        "snippet": "Increased bucket size for tier 2 users to prevent premature throttling during spikes.",
        "path": "sha:8f4a2b9",
        "meta": [
            {"icon": "commit", "text": "sha:8f4a2b9"},
            {"icon": "person", "text": "jdoe"},
        ],
        "score": 0.88,
    },
    {
        "title": "API Scaling Strategy Q3",
        "kind": "Note",
        "snippet": "...we decided to handle rate limits at the edge using Cloudflare workers before hitting...",
        "path": "vault/architecture/scaling.md",
        "meta": [{"icon": "folder", "text": "vault/architecture/scaling.md"}],
        "score": 0.81,
    },
    {
        "title": "config.yml",
        "kind": "File",
        "snippet": 'rate_limit: { enabled: true, strategy: "token_bucket", default_limit: 100 }',
        "path": "deploy/production/config.yml",
        "meta": [{"icon": "folder", "text": "deploy/production/config.yml"}],
        "score": 0.76,
    },
    {
        "title": "checkRateLimit",
        "kind": "Symbol",
        "snippet": "async function checkRateLimit(clientId: string): Promise<boolean> { ...",
        "path": "src/services/auth.ts",
        "meta": [{"icon": "folder", "text": "src/services/auth.ts"}],
        "score": 0.71,
    },
    {
        "title": "Fix rate limit bypass bug in auth flow",
        "kind": "Commit",
        "snippet": "Resolved issue where unauthenticated users were not hitting the default IP-based rate limit bucket.",
        "path": "sha:d4e5f6a",
        "meta": [{"icon": "commit", "text": "sha:d4e5f6a"}],
        "score": 0.68,
    },
]


class QueryRequest(BaseModel):
    query: str
    limit: int = Field(default=8, ge=1, le=10)


class RegisterWorkspaceRequest(BaseModel):
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
        application.state.mycelium_config = cfg
        application.state.workspace_repo = repo
        application.state.index_service = IndexService(
            data_dir=cfg.paths.data_dir,
            workspace_repo=repo,
            history_depth=cfg.index.history_depth,
        )
        yield

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

    @application.get("/health")
    def health() -> dict[str, Any]:
        cfg: MyceliumConfig | None = getattr(application.state, "mycelium_config", None)
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
        return payload

    @application.get("/workspaces")
    def list_workspaces() -> dict[str, Any]:
        return {"workspaces": workspace_repo().list_workspaces()}

    @application.post("/workspaces", status_code=201)
    def register_workspace(body: RegisterWorkspaceRequest) -> dict[str, Any]:
        try:
            row = workspace_repo().register(body.path)
        except WorkspaceError as exc:
            raise _http_error(exc) from exc
        return {"workspace": row}

    @application.post("/workspaces/{workspace_id}/index")
    def start_index(workspace_id: str) -> dict[str, Any]:
        try:
            result = index_service().run_initial_index(workspace_id)
        except WorkspaceError as exc:
            if exc.code == "not_found":
                raise HTTPException(
                    status_code=404,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            raise _http_error(exc) from exc
        except GitError as exc:
            raise _http_error(exc) from exc
        return {
            "index": {
                "workspace_id": result.workspace_id,
                "status": result.status,
                "commits_indexed": result.commits_indexed,
                "commits_total": result.commits_total,
                "depth": result.depth,
                "finished_at": result.finished_at,
                "message": result.message,
            }
        }

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

    @application.post("/query")
    def query(body: QueryRequest) -> dict[str, Any]:
        results = MOCK_RESULTS[: max(1, min(body.limit, len(MOCK_RESULTS)))]
        return {
            "query": body.query,
            "mode": "hybrid_rag",
            "count": len(results),
            "results": results,
        }

    return application


# Module-level app for `uvicorn mycelium.adapters.http.app:app` / `main:app`
app = create_app()
