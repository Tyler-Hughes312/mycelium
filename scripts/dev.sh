#!/usr/bin/env bash
# Start Mycelium Core + Desktop (Epic 5 / FR-14 recovery path).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -x "$ROOT/venv/bin/uvicorn" ]]; then
  echo "Missing venv. Run: python3 -m venv venv && ./venv/bin/pip install -e 'services/core[dev]'"
  exit 1
fi

cleanup() {
  [[ -n "${CORE_PID:-}" ]] && kill "$CORE_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting Core on 127.0.0.1:8787…"
(
  cd "$ROOT/services/core"
  "$ROOT/venv/bin/uvicorn" main:app --reload --host 127.0.0.1 --port 8787
) &
CORE_PID=$!

# Wait for health
for _ in $(seq 1 40); do
  if curl -sf http://127.0.0.1:8787/health >/dev/null; then
    echo "Core healthy."
    break
  fi
  sleep 0.25
done

echo "Starting Desktop (Vite) on http://localhost:5173 …"
cd "$ROOT/apps/desktop"
npm run dev
