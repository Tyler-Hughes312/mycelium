#!/usr/bin/env bash
# One-command local install for Mycelium (Epic 8.1 / SM-1).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Mycelium install (local-first; nothing uploaded by default)"
echo "    Privacy: code + vault stay on this machine. No cloud account required."
echo

if ! command -v python3 >/dev/null; then
  echo "Need python3 (>=3.12 recommended)."
  exit 1
fi
if ! command -v npm >/dev/null; then
  echo "Need Node.js / npm for Desktop + VS Code extension."
  exit 1
fi
if ! command -v git >/dev/null; then
  echo "Need git (workspaces must be git repos)."
  exit 1
fi

if [[ ! -d "$ROOT/venv" ]]; then
  echo "==> Creating venv…"
  python3 -m venv "$ROOT/venv"
fi

echo "==> Installing Core (editable)…"
"$ROOT/venv/bin/pip" install -U pip -q
"$ROOT/venv/bin/pip" install -e "$ROOT/services/core[dev]" -q

echo "==> Installing Desktop deps…"
(cd "$ROOT/apps/desktop" && npm install --silent)

echo "==> Installing VS Code extension deps…"
(cd "$ROOT/apps/vscode" && npm install --silent && npm run compile --silent)

echo "==> Preparing dogfood fixture repo…"
"$ROOT/scripts/prepare_dogfood.sh"

echo "==> Installing Cursor agent second-brain rule…"
mkdir -p "$ROOT/.cursor/rules"
cp "$ROOT/templates/cursor/mycelium-mcp.mdc" "$ROOT/.cursor/rules/mycelium-mcp.mdc"

echo "==> Installing MCP for Cursor / VS Code / Codex / Windsurf / Claude (+ Cursor workspaceOpen hook)…"
# Prefer user-level Cursor MCP (all projects). Avoids duplicate project+user Mycelium servers.
# shellcheck disable=SC2094
(
  cd "$ROOT/scripts"
  "$ROOT/venv/bin/python" install_mcp_clients.py \
    --repo-root "$ROOT" \
    --mycelium-mcp "$ROOT/venv/bin/mycelium-mcp"
)

echo
echo "Install complete."
echo
echo "Easy path: docs/GETTING-STARTED.md  (Desktop → vault → agents)"
echo
echo "Next (≈ first Context in <15 min):"
echo "  1. ./scripts/run-core.sh   # or Desktop app (Core on :8787; vault scaffolds at ~/.mycelium/vault)"
echo "  2. Open any git repo in Cursor — workspaceOpen auto-registers + indexes"
echo "  3. Or dogfood: Library → add: $ROOT/fixtures/dogfood-rate-limits"
echo "  4. Search: \"how did we handle rate limits\""
echo
echo "MCP clients: docs/MCP-CLIENTS.md"
echo "Production Desktop preview: ./scripts/run-desktop.sh"
echo "VS Code .vsix: cd apps/vscode && npm run package"
echo "Agents / vault: docs/AGENT-SECOND-BRAIN.md · docs/DEPLOY.md"
echo "Demo script: docs/DEMO.md"
