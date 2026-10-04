#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ -z "${RAILWAY_ENVIRONMENT:-}" && -f docker-compose.yml ]] && command -v docker >/dev/null 2>&1; then
  export COMPOSE_BAKE=false
  exec docker compose up --build
fi

if [[ -d /app/backend && -f /app/frontend/server.js ]]; then
  BACKEND_PORT="${BACKEND_PORT:-8000}"
  (cd /app/backend && uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT") &
  for _ in $(seq 1 40); do
    if curl -sf "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null; then
      break
    fi
    sleep 0.25
  done
  export HOSTNAME=0.0.0.0
  export PORT="${PORT:-3000}"
  export API_INTERNAL_URL="http://127.0.0.1:${BACKEND_PORT}"
  cd /app/frontend
  exec node server.js
fi

echo "ローカルは start.cmd / start.ps1、本番はルートの Dockerfile から起動してください。" >&2
exit 1
