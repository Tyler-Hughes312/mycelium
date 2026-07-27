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
if [[ ! -f "$ROOT/.cursor/mcp.json" ]]; then
  # Prefer absolute mycelium-mcp from this venv (IDEs often lack shell PATH).
  cat > "$ROOT/.cursor/mcp.json" <<EOF
{
  "mcpServers": {
    "mycelium": {
      "command": "$ROOT/venv/bin/mycelium-mcp",
      "args": [],
      "env": {
        "MYCELIUM_CORE_URL": "http://127.0.0.1:8787"
      }
    }
  }
}
EOF
  echo "    Wrote .cursor/mcp.json (venv mycelium-mcp; no PYTHONPATH)"
else
  echo "    Kept existing .cursor/mcp.json"
fi

echo "==> Installing user-level Cursor hooks + MCP (auto-index on workspace open)…"
# shellcheck disable=SC2094
(
  cd "$ROOT/scripts"
  "$ROOT/venv/bin/python" install_cursor_user_config.py \
    --repo-root "$ROOT" \
    --mycelium-mcp "$ROOT/venv/bin/mycelium-mcp"
)

echo
echo "Install complete."
echo
echo "Next (≈ first Context in <15 min):"
echo "  1. ./scripts/run-core.sh   # or Desktop app (Core on :8787)"
echo "  2. Open any git repo in Cursor — workspaceOpen auto-registers + indexes"
echo "  3. Or dogfood: Library → add: $ROOT/fixtures/dogfood-rate-limits"
echo "  4. Search: \"how did we handle rate limits\""
echo
echo "Production Desktop preview: ./scripts/run-desktop.sh"
echo "VS Code .vsix: cd apps/vscode && npm run package"
echo "Agents / MCP: docs/AGENT-SECOND-BRAIN.md · docs/DEPLOY.md"
echo "Demo script: docs/DEMO.md"
