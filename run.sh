#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

BACKEND_PORT="${PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

free_port() {
  local port="$1"
  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    echo "[*] Freeing port $port (killing PID(s): $pids)..."
    kill -9 $pids 2>/dev/null || true
    sleep 0.5
  fi
}

echo "[*] Clearing old processes on ports $BACKEND_PORT and $FRONTEND_PORT..."
free_port "$BACKEND_PORT"
free_port "$FRONTEND_PORT"

echo "[*] Clearing stale frontend build/cache..."
rm -rf "$FRONTEND/dist" "$FRONTEND/node_modules/.vite"

if [ ! -f "$BACKEND/.env" ]; then
  echo "[!] $BACKEND/.env missing. Copy from .env.example and fill values."
  exit 1
fi
if [ ! -f "$FRONTEND/.env" ]; then
  echo "[!] $FRONTEND/.env missing. Copy from .env.example and fill values."
  exit 1
fi

if [ ! -d "$BACKEND/.venv" ]; then
  echo "[*] Creating Python venv..."
  python3 -m venv "$BACKEND/.venv"
fi
source "$BACKEND/.venv/bin/activate"
echo "[*] Installing backend deps..."
pip install -q -r "$BACKEND/requirements.txt"

if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "[*] Installing frontend deps..."
  (cd "$FRONTEND" && npm install)
fi

cleanup() {
  echo ""
  echo "[*] Stopping..."
  kill $BACK_PID $FRONT_PID 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[*] Starting backend on http://localhost:$BACKEND_PORT ..."
(cd "$BACKEND" && uvicorn app.main:app --reload --port "$BACKEND_PORT") &
BACK_PID=$!

echo "[*] Starting frontend on http://localhost:$FRONTEND_PORT ..."
(cd "$FRONTEND" && npm run dev -- --port "$FRONTEND_PORT" --strictPort) &
FRONT_PID=$!

wait
