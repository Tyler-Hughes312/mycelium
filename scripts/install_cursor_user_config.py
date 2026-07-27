#!/usr/bin/env python3
"""Install user-level Cursor hooks + MCP for Mycelium auto-index on workspace open.

Usage:
  python scripts/install_cursor_user_config.py \\
    --repo-root /path/to/mycelium \\
    --mycelium-mcp /path/to/venv/bin/mycelium-mcp
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
from pathlib import Path

from cursor_workspace_open import (
    DEFAULT_CORE_URL,
    install_user_hooks,
    install_user_mcp,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--mycelium-mcp", type=Path, required=True)
    parser.add_argument(
        "--home",
        type=Path,
        default=Path.home(),
        help="User home (override for tests)",
    )
    parser.add_argument(
        "--core-url",
        default=os.environ.get("MYCELIUM_CORE_URL", DEFAULT_CORE_URL),
    )
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    src = repo / "scripts" / "cursor_workspace_open.py"
    if not src.is_file():
        raise SystemExit(f"Missing hook script: {src}")

    mycelium_home = args.home / ".mycelium"
    bin_dir = mycelium_home / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    dest = bin_dir / "cursor-workspace-open"
    shutil.copy2(src, dest)
    mode = dest.stat().st_mode
    dest.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    cursor_dir = args.home / ".cursor"
    hooks_path = cursor_dir / "hooks.json"
    mcp_path = cursor_dir / "mcp.json"

    install_user_hooks(hooks_path=hooks_path, script_path=dest)
    install_user_mcp(
        mcp_path=mcp_path,
        mycelium_mcp_command=str(args.mycelium_mcp.resolve()),
        core_url=str(args.core_url).strip() or DEFAULT_CORE_URL,
    )

    print(f"    Installed hook script: {dest}")
    print(f"    Merged workspaceOpen into: {hooks_path}")
    print(f"    Merged mycelium MCP into: {mcp_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
