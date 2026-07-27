#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export MYCELIUM_REPO_ROOT="$ROOT"
ENV_FILE="${MYCELIUM_HOME:-$HOME/.mycelium}/marketing/marketing.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

PYTHON="${ROOT}/venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="${PYTHON:-python3}"
fi

export PYTHONPATH="${ROOT}/services/marketing/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" -m mycelium_marketing.publisher "$@"
