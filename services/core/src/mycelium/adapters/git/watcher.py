"""Filesystem watchers that trigger incremental File/Symbol upserts (FR-4)."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from mycelium.adapters.git.files import SKIP_DIR_PARTS

if TYPE_CHECKING:
    from mycelium.core.domain.index_service import IndexService

logger = logging.getLogger(__name__)

DEBOUNCE_SEC = 0.35


class WorkspaceWatcherManager:
    """Start/stop per-workspace watchdog observers with debounce."""

    def __init__(self, index_service: IndexService) -> None:
        self._index = index_service
        self._observers: dict[str, object] = {}
        self._pending: dict[tuple[str, str], float] = {}
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None
        self._watchdog_available = True

    def start_all(self, workspaces: list[dict]) -> None:
        for ws in workspaces:
            wid = ws.get("id")
            path = ws.get("path")
            if isinstance(wid, str) and isinstance(path, str):
                self.start(wid, path)

    def start(self, workspace_id: str, root: str) -> bool:
        with self._lock:
            if workspace_id in self._observers:
                return True
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            self._watchdog_available = False
            logger.warning("watchdog not installed; file watchers disabled")
            return False

        root_path = Path(root).expanduser().resolve()
        if not root_path.is_dir():
            logger.warning("skip watcher; not a directory: %s", root_path)
            return False

        manager = self

        class Handler(FileSystemEventHandler):
            def on_modified(self, event):  # type: ignore[no-untyped-def]
                if event.is_directory:
                    return
                manager._schedule(workspace_id, str(event.src_path))

            def on_created(self, event):  # type: ignore[no-untyped-def]
                if event.is_directory:
                    return
                manager._schedule(workspace_id, str(event.src_path))

            def on_deleted(self, event):  # type: ignore[no-untyped-def]
                if event.is_directory:
                    return
                manager._schedule(workspace_id, str(event.src_path))

            def on_moved(self, event):  # type: ignore[no-untyped-def]
                if getattr(event, "dest_path", None):
                    manager._schedule(workspace_id, str(event.dest_path))
                manager._schedule(workspace_id, str(event.src_path))

        observer = Observer()
        observer.schedule(Handler(), str(root_path), recursive=True)
        observer.daemon = True
        observer.start()
        with self._lock:
            self._observers[workspace_id] = observer
        logger.info("watching workspace %s at %s", workspace_id, root_path)
        return True

    def stop(self, workspace_id: str) -> None:
        with self._lock:
            observer = self._observers.pop(workspace_id, None)
        if observer is not None:
            stop = getattr(observer, "stop", None)
            join = getattr(observer, "join", None)
            if callable(stop):
                stop()
            if callable(join):
                join(timeout=2)

    def stop_all(self) -> None:
        with self._lock:
            ids = list(self._observers.keys())
        for wid in ids:
            self.stop(wid)
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._pending.clear()

    def _schedule(self, workspace_id: str, abs_path: str) -> None:
        path = Path(abs_path)
        if any(part in SKIP_DIR_PARTS for part in path.parts):
            return
        # Ignore junk / non-source noise quickly
        if path.suffix.lower() in {".pyc", ".map", ".log", ".tmp"}:
            return
        key = (workspace_id, str(path))
        with self._lock:
            self._pending[key] = time.monotonic()
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(DEBOUNCE_SEC, self._flush)
            self._timer.daemon = True
            self._timer.start()

    def _flush(self) -> None:
        with self._lock:
            items = list(self._pending.keys())
            self._pending.clear()
            self._timer = None
        for workspace_id, abs_path in items:
            try:
                self._index.reindex_file(workspace_id, abs_path)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "incremental reindex failed for %s %s",
                    workspace_id,
                    abs_path,
                )
