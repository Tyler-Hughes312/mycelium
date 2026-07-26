"""Index orchestration — git history, symbols, co-change edges, cancellable progress."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from mycelium.adapters.git.files import language_for, list_repo_files
from mycelium.adapters.git.history import GitError, read_commit_history
from mycelium.adapters.parse.symbols import SymbolRecord, extract_symbols
from mycelium.adapters.store.commit_store import JsonCommitStore
from mycelium.adapters.store.edge_store import JsonEdgeStore
from mycelium.adapters.store.symbol_store import JsonSymbolStore
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo, WorkspaceError
from mycelium.core.domain.co_change import build_co_changed_edges
from mycelium.core.domain.embedding_service import EmbeddingService
from mycelium.core.ports.embedding_runtime import EmbeddingRuntime
from mycelium.adapters.embeddings.bootstrap import EmbeddingStatus


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class IndexCancelled(Exception):
    """Raised when an index run is cancelled mid-flight."""


@dataclass
class IndexResult:
    workspace_id: str
    status: str
    commits_indexed: int
    commits_total: int
    files_indexed: int
    symbols_indexed: int
    edges_indexed: int
    vectors_indexed: int
    depth: int
    finished_at: str
    message: str


class IndexService:
    def __init__(
        self,
        *,
        data_dir: Path,
        workspace_repo: JsonFileWorkspaceRepo,
        history_depth: int = 500,
        embedding_runtime: EmbeddingRuntime | None = None,
        embedding_status: EmbeddingStatus | None = None,
        embedding_model: str = "mycelium-hashing-v1",
    ) -> None:
        self._data_dir = data_dir
        self._workspaces = workspace_repo
        self._history_depth = history_depth
        self._status_dir = data_dir / "index_status"
        self._status_dir.mkdir(parents=True, exist_ok=True)
        self._cancel_events: dict[str, threading.Event] = {}
        self._lock = threading.Lock()
        self._running: set[str] = set()
        self._embedder = EmbeddingService(
            data_dir=data_dir,
            workspace_repo=workspace_repo,
            runtime=embedding_runtime,
            status=embedding_status,
            model=embedding_model,
        )

    @property
    def embedding_service(self) -> EmbeddingService:
        return self._embedder

    def _workspace_dir(self, workspace_id: str) -> Path:
        return self._data_dir / "workspaces" / workspace_id

    def _status_path(self, workspace_id: str) -> Path:
        return self._status_dir / f"{workspace_id}.json"

    def get_status(self, workspace_id: str) -> dict[str, Any] | None:
        path = self._status_path(workspace_id)
        if not path.exists():
            return None
        import json

        return json.loads(path.read_text(encoding="utf-8"))

    def _write_status(self, workspace_id: str, payload: dict[str, Any]) -> None:
        import json

        self._status_path(workspace_id).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def is_running(self, workspace_id: str) -> bool:
        with self._lock:
            return workspace_id in self._running

    def request_cancel(self, workspace_id: str) -> dict[str, Any]:
        """Signal cancel; in-flight writer skips final snapshot (AD-7 safe)."""
        with self._lock:
            event = self._cancel_events.get(workspace_id)
            running = workspace_id in self._running
        if event is not None:
            event.set()
        status = self.get_status(workspace_id) or {
            "workspace_id": workspace_id,
            "status": "idle",
            "progress": 0,
        }
        if running:
            status = {
                **status,
                "status": "cancelling",
                "message": "Cancel requested…",
            }
            self._write_status(workspace_id, status)
        return status

    def start_index_async(self, workspace_id: str) -> dict[str, Any]:
        """Start indexing in a background thread; return current status."""
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            raise WorkspaceError("not_found", f"Unknown workspace id: {workspace_id}")

        with self._lock:
            if workspace_id in self._running:
                return self.get_status(workspace_id) or {
                    "workspace_id": workspace_id,
                    "status": "indexing",
                    "progress": 0,
                    "message": "Index already running",
                }
            cancel = threading.Event()
            self._cancel_events[workspace_id] = cancel
            self._running.add(workspace_id)

        started = _now_iso()
        self._workspaces.update(workspace_id, {"status": "indexing"})
        self._write_status(
            workspace_id,
            {
                "workspace_id": workspace_id,
                "status": "indexing",
                "phase": "starting",
                "progress": 1,
                "started_at": started,
                "message": "Starting index…",
                "cancellable": True,
            },
        )

        thread = threading.Thread(
            target=self._run_safe,
            args=(workspace_id, cancel, started),
            daemon=True,
            name=f"mycelium-index-{workspace_id[:8]}",
        )
        thread.start()
        return self.get_status(workspace_id) or {}

    def run_initial_index(self, workspace_id: str) -> IndexResult:
        """Synchronous index (tests / scripts)."""
        cancel = threading.Event()
        with self._lock:
            self._cancel_events[workspace_id] = cancel
            self._running.add(workspace_id)
        started = _now_iso()
        try:
            return self._run_index(workspace_id, cancel.is_set, started)
        finally:
            with self._lock:
                self._running.discard(workspace_id)
                self._cancel_events.pop(workspace_id, None)

    def _run_safe(
        self,
        workspace_id: str,
        cancel: threading.Event,
        started: str,
    ) -> None:
        try:
            self._run_index(workspace_id, cancel.is_set, started)
        except IndexCancelled:
            prev = self.get_status(workspace_id) or {}
            self._workspaces.update(workspace_id, {"status": "idle"})
            self._write_status(
                workspace_id,
                {
                    "workspace_id": workspace_id,
                    "status": "cancelled",
                    "phase": "cancelled",
                    "progress": int(prev.get("progress") or 0),
                    "started_at": started,
                    "finished_at": _now_iso(),
                    "message": "Index cancelled — prior symbol/edge snapshot preserved if present",
                    "cancellable": False,
                },
            )
        except GitError as exc:
            self._workspaces.update(workspace_id, {"status": "idle"})
            self._write_status(
                workspace_id,
                {
                    "workspace_id": workspace_id,
                    "status": "failed",
                    "phase": "git_history",
                    "progress": 0,
                    "started_at": started,
                    "finished_at": _now_iso(),
                    "error": {"code": exc.code, "message": exc.message},
                    "message": exc.message,
                    "cancellable": False,
                },
            )
        except Exception as exc:  # noqa: BLE001 — surface unexpected failures in status
            self._workspaces.update(workspace_id, {"status": "idle"})
            self._write_status(
                workspace_id,
                {
                    "workspace_id": workspace_id,
                    "status": "failed",
                    "phase": "error",
                    "progress": 0,
                    "started_at": started,
                    "finished_at": _now_iso(),
                    "error": {"code": "internal_error", "message": str(exc)},
                    "message": str(exc),
                    "cancellable": False,
                },
            )
        finally:
            with self._lock:
                self._running.discard(workspace_id)
                self._cancel_events.pop(workspace_id, None)

    def _check(self, cancelled: Callable[[], bool]) -> None:
        if cancelled():
            raise IndexCancelled()

    def _run_index(
        self,
        workspace_id: str,
        cancelled: Callable[[], bool],
        started: str,
    ) -> IndexResult:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            raise WorkspaceError("not_found", f"Unknown workspace id: {workspace_id}")

        repo_path = Path(ws["path"])
        workspace_dir = self._workspace_dir(workspace_id)
        self._workspaces.update(workspace_id, {"status": "indexing"})

        def status(**kwargs: Any) -> None:
            payload = {
                "workspace_id": workspace_id,
                "started_at": started,
                "cancellable": True,
                **kwargs,
            }
            self._write_status(workspace_id, payload)

        self._check(cancelled)
        status(
            status="indexing",
            phase="git_history",
            progress=10,
            message="Reading git history…",
        )
        commits = read_commit_history(repo_path, depth=self._history_depth)
        self._check(cancelled)
        commit_total = JsonCommitStore(workspace_dir).upsert_commits(commits)

        status(
            status="indexing",
            phase="symbols",
            progress=35,
            message="Parsing symbols…",
            commits_indexed=len(commits),
            commits_total=commit_total,
        )
        files_indexed, symbols_indexed, symbol_records = self._ingest_symbols(
            repo_path,
            workspace_dir,
            cancelled,
            on_progress=lambda pct, msg: status(
                status="indexing",
                phase="symbols",
                progress=35 + int(pct * 0.4),
                message=msg,
                commits_indexed=len(commits),
                commits_total=commit_total,
            ),
        )

        self._check(cancelled)
        status(
            status="indexing",
            phase="co_change",
            progress=80,
            message="Building co-change edges…",
            commits_indexed=len(commits),
            commits_total=commit_total,
            files_indexed=files_indexed,
            symbols_indexed=symbols_indexed,
        )
        edges = build_co_changed_edges(commits, symbol_records)
        self._check(cancelled)
        edges_indexed = JsonEdgeStore(workspace_dir).replace_snapshot(edges)

        self._check(cancelled)
        status(
            status="indexing",
            phase="embeddings",
            progress=90,
            message=self._embedder.status.notice,
            commits_indexed=len(commits),
            commits_total=commit_total,
            files_indexed=files_indexed,
            symbols_indexed=symbols_indexed,
            edges_indexed=edges_indexed,
        )
        embed_stats = self._embedder.embed_workspace(workspace_id)
        vectors_indexed = int(embed_stats.get("vectors") or 0)

        finished = _now_iso()
        self._workspaces.update(
            workspace_id,
            {
                "status": "healthy",
                "commits": commit_total,
                "symbols": symbols_indexed,
                "indexed_ago": "just now",
                "last_indexed_at": finished,
            },
        )
        result = IndexResult(
            workspace_id=workspace_id,
            status="complete",
            commits_indexed=len(commits),
            commits_total=commit_total,
            files_indexed=files_indexed,
            symbols_indexed=symbols_indexed,
            edges_indexed=edges_indexed,
            vectors_indexed=vectors_indexed,
            depth=self._history_depth,
            finished_at=finished,
            message=(
                f"Indexed {len(commits)} commits, {files_indexed} files, "
                f"{symbols_indexed} symbols, {edges_indexed} co-change edges, "
                f"{vectors_indexed} vectors"
            ),
        )
        status(
            status="complete",
            phase="complete",
            progress=100,
            finished_at=finished,
            commits_indexed=result.commits_indexed,
            commits_total=result.commits_total,
            files_indexed=result.files_indexed,
            symbols_indexed=result.symbols_indexed,
            edges_indexed=result.edges_indexed,
            vectors_indexed=result.vectors_indexed,
            message=result.message,
            embedding_notice=self._embedder.status.notice,
            cancellable=False,
        )
        return result

    def _ingest_symbols(
        self,
        repo_path: Path,
        workspace_dir: Path,
        cancelled: Callable[[], bool],
        *,
        on_progress: Callable[[float, str], None],
    ) -> tuple[int, int, list[SymbolRecord]]:
        rels = list_repo_files(repo_path)
        file_nodes: list[dict[str, Any]] = []
        symbols: list[SymbolRecord] = []
        total = max(len(rels), 1)

        for i, rel in enumerate(rels):
            self._check(cancelled)
            if i % 25 == 0 or i + 1 == total:
                on_progress(i / total, f"Parsing symbols… ({i}/{len(rels)} files)")
            abs_path = repo_path / rel
            lang = language_for(rel)
            path_str = rel.as_posix()
            file_nodes.append(
                {
                    "id": f"file:{path_str}",
                    "kind": "File",
                    "path": path_str,
                    "language": lang,
                    "has_symbols": lang is not None,
                }
            )
            if lang is None:
                continue
            try:
                source = abs_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            symbols.extend(extract_symbols(repo_path, rel, source))

        self._check(cancelled)
        # Atomic-ish final write: only persist symbols/files if not cancelled.
        files_count, symbols_count = JsonSymbolStore(workspace_dir).replace_snapshot(
            files=file_nodes,
            symbols=symbols,
        )
        return files_count, symbols_count, symbols

    def list_commits(self, workspace_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            raise WorkspaceError("not_found", f"Unknown workspace id: {workspace_id}")
        return JsonCommitStore(self._workspace_dir(workspace_id)).list_commits(limit=limit)

    def list_symbols(self, workspace_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            raise WorkspaceError("not_found", f"Unknown workspace id: {workspace_id}")
        return JsonSymbolStore(self._workspace_dir(workspace_id)).list_symbols(limit=limit)

    def list_edges(
        self,
        workspace_id: str,
        *,
        kind: str | None = "co_changed",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            raise WorkspaceError("not_found", f"Unknown workspace id: {workspace_id}")
        return JsonEdgeStore(self._workspace_dir(workspace_id)).list_edges(
            kind=kind,
            limit=limit,
        )

    def reindex_file(self, workspace_id: str, path: str) -> dict[str, Any]:
        """
        Incremental File/Symbol upsert for one path (FR-4 / AD-7).
        Accepts absolute or workspace-relative paths.
        """
        import time

        ws = self._workspaces.get(workspace_id)
        if ws is None:
            raise WorkspaceError("not_found", f"Unknown workspace id: {workspace_id}")

        repo_path = Path(ws["path"]).resolve()
        rel = self._resolve_rel_path(repo_path, path)
        abs_path = repo_path / rel
        path_str = rel.as_posix()
        store = JsonSymbolStore(self._workspace_dir(workspace_id))
        started = time.perf_counter()

        if not abs_path.exists():
            files_n, symbols_n = store.upsert_file_symbols(
                file_node=None,
                path=path_str,
                symbols=[],
                deleted=True,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            self._workspaces.update(
                workspace_id,
                {
                    "symbols": symbols_n,
                    "indexed_ago": "just now",
                    "last_indexed_at": _now_iso(),
                },
            )
            return {
                "workspace_id": workspace_id,
                "path": path_str,
                "deleted": True,
                "symbols_upserted": 0,
                "files_total": files_n,
                "symbols_total": symbols_n,
                "elapsed_ms": round(elapsed_ms, 2),
                "stable_ids": True,
            }

        if not abs_path.is_file():
            raise WorkspaceError("not_file", f"Path is not a file: {abs_path}")

        lang = language_for(rel)
        file_node = {
            "id": f"file:{path_str}",
            "kind": "File",
            "path": path_str,
            "language": lang,
            "has_symbols": lang is not None,
        }
        symbols: list[SymbolRecord] = []
        if lang is not None:
            try:
                source = abs_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise WorkspaceError("read_failed", str(exc)) from exc
            symbols = extract_symbols(repo_path, rel, source)

        # Capture IDs before write for stability assertion helpers.
        symbol_ids = [s.node_id for s in symbols]
        files_n, symbols_n = store.upsert_file_symbols(
            file_node=file_node,
            path=path_str,
            symbols=symbols,
            deleted=False,
        )
        symbol_rows = [
            {
                "id": s.node_id,
                "name": s.name,
                "path": s.path,
                "symbol_kind": s.kind,
                "language": s.language,
            }
            for s in symbols
        ]
        embed_stats = self._embedder.embed_symbols(workspace_id, symbol_rows)
        elapsed_ms = (time.perf_counter() - started) * 1000
        self._workspaces.update(
            workspace_id,
            {
                "symbols": symbols_n,
                "indexed_ago": "just now",
                "last_indexed_at": _now_iso(),
            },
        )
        return {
            "workspace_id": workspace_id,
            "path": path_str,
            "deleted": False,
            "language": lang,
            "symbols_upserted": len(symbols),
            "symbol_ids": symbol_ids,
            "files_total": files_n,
            "symbols_total": symbols_n,
            "vectors_written": embed_stats.get("written", 0),
            "elapsed_ms": round(elapsed_ms, 2),
            "stable_ids": True,
        }

    @staticmethod
    def _resolve_rel_path(repo_path: Path, path: str) -> Path:
        raw = Path(path).expanduser()
        if raw.is_absolute():
            try:
                return raw.resolve().relative_to(repo_path)
            except ValueError as exc:
                raise WorkspaceError(
                    "outside_workspace",
                    f"Path is outside workspace root: {raw}",
                ) from exc
        rel = Path(path.replace("\\", "/"))
        # Prevent escape via ..
        resolved = (repo_path / rel).resolve()
        try:
            return resolved.relative_to(repo_path)
        except ValueError as exc:
            raise WorkspaceError(
                "outside_workspace",
                f"Path is outside workspace root: {path}",
            ) from exc
