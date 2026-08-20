#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

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

echo "[*] Starting backend on http://localhost:8000 ..."
(cd "$BACKEND" && uvicorn app.main:app --reload --port 8000) &
BACK_PID=$!

echo "[*] Starting frontend on http://localhost:5173 ..."
(cd "$FRONTEND" && npm run dev) &
FRONT_PID=$!

wait
