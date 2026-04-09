#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

cleanup() {
  echo ""
  echo "Stopping servers..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

PIDS=()

echo "==> API: http://127.0.0.1:8000  (docs: /docs)"
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload &
PIDS+=("$!")

sleep 1

echo "==> Web: http://localhost:4200"

export NG_CLI_ANALYTICS=false
(cd "$ROOT/web" && npm start) &
PIDS+=("$!")

echo ""
echo "Both processes running. Press Ctrl+C to stop."
wait
