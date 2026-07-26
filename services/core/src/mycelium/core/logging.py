"""Structured logging for Mycelium Core (stderr + ~/.mycelium/logs/)."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


def setup_logging(logs_dir: Path | None = None, *, level: int = logging.INFO) -> Path:
    """Configure root logger: stderr + rotating daily file under logs_dir.

    Returns the log file path used for this process (or logs_dir if file setup fails).
    """
    root = logging.getLogger()
    if getattr(root, "_mycelium_configured", False):
        return Path(getattr(root, "_mycelium_log_file", logs_dir or Path(".")))

    root.setLevel(level)
    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    stderr = logging.StreamHandler(sys.stderr)
    stderr.setFormatter(fmt)
    stderr.setLevel(level)
    root.addHandler(stderr)

    log_file = Path(".")
    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = logs_dir / f"core-{stamp}.log"
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(fmt)
            file_handler.setLevel(level)
            root.addHandler(file_handler)
        except OSError:
            logging.getLogger(__name__).warning(
                "Could not open log file %s; stderr only", log_file
            )

    root._mycelium_configured = True  # type: ignore[attr-defined]
    root._mycelium_log_file = str(log_file)  # type: ignore[attr-defined]
    return log_file


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
