#!/usr/bin/env python3
"""Install Mycelium MCP into common IDE / agent clients + Cursor workspaceOpen hook.

Usage:
  python scripts/install_mcp_clients.py \\
    --repo-root /path/to/mycelium \\
    --mycelium-mcp /path/to/venv/bin/mycelium-mcp
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path

# Allow importing sibling modules when run from scripts/
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cursor_workspace_open import (  # noqa: E402
    DEFAULT_CORE_URL,
    install_user_hooks,
    install_user_mcp,
)
from mcp_clients import (  # noqa: E402
    claude_desktop_config_path,
    codex_config_path,
    install_codex,
    install_json_client,
    remove_mycelium_from_mcp_servers,
    vscode_user_mcp_paths,
    windsurf_mcp_path,
    write_json,
    merge_vscode_mcp_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--mycelium-mcp", type=Path, required=True)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument(
        "--core-url",
        default=os.environ.get("MYCELIUM_CORE_URL", DEFAULT_CORE_URL),
    )
    parser.add_argument(
        "--keep-project-cursor-mcp",
        action="store_true",
        help="Do not remove mycelium from the repo .cursor/mcp.json (avoids Cursor duplicate by default)",
    )
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    command = str(args.mycelium_mcp.resolve())
    core_url = str(args.core_url).strip() or DEFAULT_CORE_URL
    home = args.home

    # Hook script
    src = repo / "scripts" / "cursor_workspace_open.py"
    if not src.is_file():
        raise SystemExit(f"Missing hook script: {src}")
    bin_dir = home / ".mycelium" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    dest = bin_dir / "cursor-workspace-open"
    shutil.copy2(src, dest)
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    installed: list[str] = []

    # Cursor user MCP + hooks
    cursor_dir = home / ".cursor"
    install_user_hooks(hooks_path=cursor_dir / "hooks.json", script_path=dest)
    install_user_mcp(
        mcp_path=cursor_dir / "mcp.json",
        mycelium_mcp_command=command,
        core_url=core_url,
    )
    installed.append(f"Cursor user MCP+hooks → {cursor_dir}")

    # Deduplicate project Cursor MCP (user-level is enough for all repos)
    project_mcp = repo / ".cursor" / "mcp.json"
    if not args.keep_project_cursor_mcp and remove_mycelium_from_mcp_servers(project_mcp):
        installed.append(f"Removed duplicate mycelium from {project_mcp}")

    # VS Code / Copilot user mcp.json (+ Insiders) — only if the app User dir exists
    for path in vscode_user_mcp_paths(home):
        if path.parent.is_dir():
            install_json_client(path, command=command, core_url=core_url, kind="vscode")
            installed.append(f"VS Code/Copilot → {path}")

    # Workspace VS Code / Copilot MCP (Agent mode)
    data = merge_vscode_mcp_json(None, command=command, core_url=core_url)
    write_json(repo / ".vscode" / "mcp.json", data)
    installed.append(f"VS Code workspace → {repo / '.vscode' / 'mcp.json'}")

    # Windsurf — write under ~/.codeium/windsurf (create parents)
    ws_path = windsurf_mcp_path(home)
    install_json_client(ws_path, command=command, core_url=core_url, kind="mcpServers")
    installed.append(f"Windsurf → {ws_path}")

    # Claude Desktop — only if Claude app config dir exists
    claude_path = claude_desktop_config_path(home)
    if claude_path is not None and claude_path.parent.is_dir():
        install_json_client(
            claude_path, command=command, core_url=core_url, kind="mcpServers"
        )
        installed.append(f"Claude Desktop → {claude_path}")
    elif claude_path is not None:
        installed.append(
            f"Claude Desktop skipped (install Claude app, then re-run). Template: "
            f"templates/claude-desktop/"
        )

    # Codex
    codex_path = codex_config_path(home)
    install_codex(codex_path, command=command, core_url=core_url)
    installed.append(f"Codex → {codex_path}")

    print("    Mycelium MCP clients:")
    for line in installed:
        print(f"      • {line}")
    print()
    print("    Claude Code (CLI) — run once:")
    print(f'      claude mcp add mycelium --env MYCELIUM_CORE_URL={core_url} -- "{command}"')
    print()
    print("    Docs: docs/MCP-CLIENTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
