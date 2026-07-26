#!/usr/bin/env bash
# Production Core launcher (no --reload). Logs → stderr + ~/.mycelium/logs/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/venv/bin/mycelium" ]]; then
  exec "$ROOT/venv/bin/mycelium" serve "$@"
fi

if command -v mycelium >/dev/null 2>&1; then
  exec mycelium serve "$@"
fi

echo "mycelium not found. Install: pip install -e 'services/core[dev]'" >&2
exit 1
