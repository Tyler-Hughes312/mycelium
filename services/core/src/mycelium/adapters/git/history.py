"""Git history reader — Commit Node source for indexing (FR-5)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommitRecord:
    hash: str
    author: str
    timestamp: str
    message: str
    changed_paths: tuple[str, ...]


class GitError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def read_commit_history(repo_path: Path, *, depth: int = 500) -> list[CommitRecord]:
    """Read up to `depth` commits with changed paths via `git log`."""
    if depth < 1:
        raise GitError("invalid_depth", "history depth must be >= 1")
    if not (repo_path / ".git").exists():
        raise GitError("not_git_repo", f"Not a git repository: {repo_path}")

    # Header marker keeps name-only paths associated with the correct commit.
    pretty = ">>>%H%x1f%an%x1f%aI%x1f%s"
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(repo_path),
                "log",
                f"-n{depth}",
                f"--pretty=format:{pretty}",
                "--name-only",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitError("git_missing", "git executable not found on PATH") from exc

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "git log failed").strip()
        raise GitError("git_log_failed", err)

    return _parse_log(proc.stdout)


def _parse_log(stdout: str) -> list[CommitRecord]:
    records: list[CommitRecord] = []
    current_header: tuple[str, str, str, str] | None = None
    paths: list[str] = []

    def flush() -> None:
        nonlocal current_header, paths
        if current_header is None:
            return
        commit_hash, author, timestamp, message = current_header
        records.append(
            CommitRecord(
                hash=commit_hash,
                author=author,
                timestamp=timestamp,
                message=message,
                changed_paths=tuple(paths),
            )
        )
        current_header = None
        paths = []

    for raw in stdout.splitlines():
        line = raw.strip("\r")
        if line.startswith(">>>"):
            flush()
            parts = line[3:].split("\x1f")
            if len(parts) < 4:
                continue
            current_header = (
                parts[0].strip(),
                parts[1].strip(),
                parts[2].strip(),
                parts[3].strip(),
            )
            paths = []
        elif line.strip() and current_header is not None:
            paths.append(line.strip())

    flush()
    return records
