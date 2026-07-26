"""List workspace source files for indexing."""

from __future__ import annotations

import subprocess
from pathlib import Path

SKIP_DIR_PARTS = {
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    ".git",
    "__pycache__",
    ".pytest_cache",
    "out",
    ".mypy_cache",
    "coverage",
    ".turbo",
}

SUPPORTED_LANG = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".go": "go",
}

MAX_FILE_BYTES = 5 * 1024 * 1024


def language_for(path: Path) -> str | None:
    return SUPPORTED_LANG.get(path.suffix.lower())


def list_repo_files(repo_path: Path) -> list[Path]:
    """Return relative Paths of tracked (or walked) files, excluding junk dirs."""
    rels = _git_ls_files(repo_path)
    if rels is None:
        rels = _walk_files(repo_path)

    out: list[Path] = []
    for rel in rels:
        if any(part in SKIP_DIR_PARTS for part in rel.parts):
            continue
        abs_path = repo_path / rel
        if not abs_path.is_file():
            continue
        try:
            if abs_path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        out.append(rel)
    return out


def _git_ls_files(repo_path: Path) -> list[Path] | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "ls-files"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    return [Path(line) for line in proc.stdout.splitlines() if line.strip()]


def git_head(repo_path: Path) -> str | None:
    """Current HEAD commit hash, or None if not a git repo / error."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip()
    return sha or None


def git_dirty_paths(repo_path: Path, *, limit: int = 80) -> list[str]:
    """Working-tree paths that differ from HEAD (modified / added / untracked)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "status", "--porcelain", "-u"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    out: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path_part = line[3:] if len(line) > 3 else line
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]
        path_part = path_part.strip().strip('"')
        if not path_part:
            continue
        rel = Path(path_part)
        if any(part in SKIP_DIR_PARTS for part in rel.parts):
            continue
        out.append(rel.as_posix())
        if len(out) >= limit:
            break
    return out


def _walk_files(repo_path: Path) -> list[Path]:
    rows: list[Path] = []
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(repo_path)
        except ValueError:
            continue
        if any(part in SKIP_DIR_PARTS for part in rel.parts):
            continue
        rows.append(rel)
    return rows
