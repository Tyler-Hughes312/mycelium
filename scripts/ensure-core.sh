#!/usr/bin/env bash
# Ensure Mycelium Core is listening on 127.0.0.1:8787 (for MCP / browser / VS Code).
# Prefer: open the Mycelium desktop app (it starts Core and leaves it running).
# This script is for when Desktop is not open.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
URL="${MYCELIUM_CORE_URL:-http://127.0.0.1:8787}"

if curl -sf "$URL/health" >/dev/null 2>&1; then
  echo "Core already online at $URL"
  curl -s "$URL/health" | head -c 200
  echo
  exit 0
fi

echo "Core offline — starting…"
exec "$ROOT/scripts/run-core.sh" "$@"
