"""Index orchestration — Story 2.2 git history ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mycelium.adapters.git.history import GitError, read_commit_history
from mycelium.adapters.store.commit_store import JsonCommitStore
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo, WorkspaceError


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class IndexResult:
    workspace_id: str
    status: str
    commits_indexed: int
    commits_total: int
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
    ) -> None:
        self._data_dir = data_dir
        self._workspaces = workspace_repo
        self._history_depth = history_depth
        self._status_dir = data_dir / "index_status"
        self._status_dir.mkdir(parents=True, exist_ok=True)

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

    def run_initial_index(self, workspace_id: str) -> IndexResult:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            raise WorkspaceError("not_found", f"Unknown workspace id: {workspace_id}")

        repo_path = Path(ws["path"])
        self._workspaces.update(workspace_id, {"status": "indexing"})
        started = _now_iso()
        self._write_status(
            workspace_id,
            {
                "workspace_id": workspace_id,
                "status": "indexing",
                "phase": "git_history",
                "progress": 0,
                "started_at": started,
                "message": "Reading git history…",
            },
        )

        try:
            commits = read_commit_history(repo_path, depth=self._history_depth)
            store = JsonCommitStore(self._workspace_dir(workspace_id))
            total = store.upsert_commits(commits)
            finished = _now_iso()
            self._workspaces.update(
                workspace_id,
                {
                    "status": "healthy",
                    "commits": total,
                    "indexed_ago": "just now",
                    "last_indexed_at": finished,
                },
            )
            result = IndexResult(
                workspace_id=workspace_id,
                status="complete",
                commits_indexed=len(commits),
                commits_total=total,
                depth=self._history_depth,
                finished_at=finished,
                message=f"Indexed {len(commits)} commits (store total {total})",
            )
            self._write_status(
                workspace_id,
                {
                    "workspace_id": workspace_id,
                    "status": "complete",
                    "phase": "git_history",
                    "progress": 100,
                    "started_at": started,
                    "finished_at": finished,
                    "commits_indexed": result.commits_indexed,
                    "commits_total": result.commits_total,
                    "message": result.message,
                },
            )
            return result
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
                },
            )
            raise

    def list_commits(self, workspace_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        ws = self._workspaces.get(workspace_id)
        if ws is None:
            raise WorkspaceError("not_found", f"Unknown workspace id: {workspace_id}")
        return JsonCommitStore(self._workspace_dir(workspace_id)).list_commits(limit=limit)
