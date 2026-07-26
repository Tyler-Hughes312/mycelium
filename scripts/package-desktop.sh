#!/usr/bin/env bash
# Build downloadable Mycelium Desktop (Core sidecar + Tauri bundle).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f "$HOME/.cargo/env" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.cargo/env"
fi

if ! command -v cargo >/dev/null 2>&1; then
  echo "Rust/cargo required. Install: https://rustup.rs" >&2
  exit 1
fi

if [[ ! -d "$ROOT/apps/desktop/node_modules" ]]; then
  echo "==> npm install (desktop)"
  (cd "$ROOT/apps/desktop" && npm install)
fi

echo "==> Building Core sidecar"
bash "$ROOT/scripts/build-core-sidecar.sh"

echo "==> Tauri build"
(cd "$ROOT/apps/desktop" && npm run tauri:build)

BUNDLE="$ROOT/apps/desktop/src-tauri/target/release/bundle"
echo
echo "Done. Artifacts under:"
echo "  $BUNDLE"
ls -la "$BUNDLE" 2>/dev/null || true
find "$BUNDLE" -maxdepth 3 \( -name '*.dmg' -o -name '*.app' -o -name '*.exe' -o -name '*.msi' \) 2>/dev/null || true
