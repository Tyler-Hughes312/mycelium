#!/usr/bin/env bash
# Build mycelium-core (PyInstaller onedir) into Tauri resources/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CORE="$ROOT/services/core"
SPEC="$CORE/packaging/mycelium-core.spec"
OUT_DIR="$CORE/packaging/dist"
RES_DIR="$ROOT/apps/desktop/src-tauri/resources/mycelium-core"

if [[ -x "$ROOT/venv/bin/python" ]]; then
  PYTHON="$ROOT/venv/bin/python"
  PIP="$ROOT/venv/bin/pip"
elif [[ -x "$ROOT/venv/Scripts/python.exe" ]]; then
  PYTHON="$ROOT/venv/Scripts/python.exe"
  PIP="$ROOT/venv/Scripts/pip.exe"
else
  echo "No project venv. Run ./scripts/install.sh first." >&2
  exit 1
fi

echo "==> Ensuring PyInstaller + Core editable install"
"$PIP" install -q -U "pyinstaller>=6.0"
"$PIP" install -q -e "$CORE"

echo "==> Building sidecar (PyInstaller onedir)"
rm -rf "$CORE/packaging/build" "$OUT_DIR"
(
  cd "$CORE/packaging"
  "$PYTHON" -m PyInstaller --noconfirm --clean "$SPEC"
)

SIDECAR_DIR="$OUT_DIR/mycelium-core"
if [[ ! -d "$SIDECAR_DIR" ]]; then
  echo "PyInstaller output missing: $SIDECAR_DIR" >&2
  exit 1
fi

echo "==> Staging into Tauri resources"
rm -rf "$RES_DIR"
mkdir -p "$(dirname "$RES_DIR")"
cp -R "$SIDECAR_DIR" "$RES_DIR"

if [[ -f "$RES_DIR/mycelium-core" ]]; then
  chmod +x "$RES_DIR/mycelium-core"
fi
if [[ -f "$RES_DIR/mycelium-core.exe" ]]; then
  echo "    Windows exe present"
fi

echo "==> Sidecar ready at $RES_DIR"
du -sh "$RES_DIR" || true
