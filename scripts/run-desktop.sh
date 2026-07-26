#!/usr/bin/env bash
# Serve the production Desktop build (vite preview) against local Core.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/desktop"

if [[ ! -d node_modules ]]; then
  echo "Installing Desktop deps…"
  npm install
fi

if [[ ! -d dist ]]; then
  echo "Building Desktop…"
  npm run build
fi

echo "Desktop preview → http://127.0.0.1:4173 (Core must be on :8787)"
echo "  Start Core: ./scripts/run-core.sh"
exec npm run preview -- --host 127.0.0.1 --port 4173
