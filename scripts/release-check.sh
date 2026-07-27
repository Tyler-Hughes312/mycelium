#!/usr/bin/env bash
# Local CI-equivalent gate before tagging a release.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0

echo "==> Core pytest"
if [[ -x "$ROOT/venv/bin/pytest" ]]; then
  (cd "$ROOT/services/core" && "$ROOT/venv/bin/pytest" -q) || fail=1
else
  (cd "$ROOT/services/core" && python3 -m pytest -q) || fail=1
fi

echo "==> Desktop lint + build"
(cd "$ROOT/apps/desktop" && npm run lint && npm run build) || fail=1

echo "==> VS Code compile"
(cd "$ROOT/apps/vscode" && npm run compile) || fail=1

echo "==> Console scripts present (venv)"
if [[ -x "$ROOT/venv/bin/mycelium" && -x "$ROOT/venv/bin/mycelium-mcp" ]]; then
  "$ROOT/venv/bin/mycelium" --version || fail=1
else
  echo "    (skip: reinstall with pip install -e services/core[dev])"
fi

echo "==> VSIX package (optional dry-run compile already done)"
if [[ -x "$ROOT/apps/vscode/node_modules/.bin/vsce" ]] || [[ -d "$ROOT/apps/vscode/node_modules/@vscode/vsce" ]]; then
  (cd "$ROOT/apps/vscode" && npm run package) || fail=1
else
  echo "    Installing vsce for package…"
  (cd "$ROOT/apps/vscode" && npm install --no-save @vscode/vsce && npm run package) || fail=1
fi

echo "==> Marketing site test + build"
(cd "$ROOT/apps/web" && npm test && npm run build) || fail=1

if [[ "$fail" -ne 0 ]]; then
  echo
  echo "release-check FAILED"
  exit 1
fi

echo
echo "release-check OK — Core/Desktop/VS Code/Web gate passed (current Desktop: 0.1.3)"
