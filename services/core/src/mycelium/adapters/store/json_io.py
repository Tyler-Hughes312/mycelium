"""Atomic / resilient JSON file helpers for local Graph stores."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


@contextmanager
def file_lock(path: Path) -> Iterator[None]:
    """Exclusive flock beside the target file (best-effort on POSIX)."""
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a", encoding="utf-8") as lock_f:
        try:
            import fcntl

            fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        try:
            yield
        finally:
            try:
                import fcntl

                fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
            except (ImportError, OSError):
                pass


def read_json_object(path: Path, *, default: Any | None = None) -> Any:
    """
    Load a JSON object from disk.

    If the file was torn (concurrent non-atomic writes), recover the first
    complete JSON value and rewrite a clean file when possible.
    """
    if default is None:
        default = {}
    if not path.exists():
        return default
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return default
    try:
        data = json.loads(raw)
        return data if data is not None else default
    except json.JSONDecodeError:
        dec = json.JSONDecoder()
        try:
            data, end = dec.raw_decode(raw)
        except json.JSONDecodeError:
            return default
        # Recovered prefix — rewrite cleanly under lock
        if isinstance(data, (dict, list)):
            try:
                with file_lock(path):
                    atomic_write_json(path, data)
            except OSError:
                pass
        return data if data is not None else default


def atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON via temp file + os.replace (no torn reads of partial JSON)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
