#!/usr/bin/env bash
# One-shot setup + start for the vvaharness console.
#
# Usage:
#   From an existing clone:  ./start.sh
#   From anywhere (clones into ./vvaharness-console first):
#     curl -fsSL https://raw.githubusercontent.com/hicmoo/vvaharness-console/main/start.sh | bash
#
# Starts the backend on http://127.0.0.1:8000 and the frontend on
# http://127.0.0.1:5173. Ctrl+C stops both.

set -euo pipefail

REPO_URL="https://github.com/hicmoo/vvaharness-console.git"

err() { echo "error: $*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || err "git is required"
command -v npm >/dev/null 2>&1 || err "npm is required (install Node 20+ from https://nodejs.org)"

find_python() {
  for cand in "${PYTHON:-}" python3.13 python3.12 python3.11 python3; do
    [ -n "$cand" ] || continue
    command -v "$cand" >/dev/null 2>&1 || continue
    if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
      echo "$cand"
      return 0
    fi
  done
  return 1
}

# Locate or clone the repo.
if [ -f "backend/pyproject.toml" ] && [ -f "frontend/package.json" ]; then
  : # already at the repo root
elif [ -d "vvaharness-console" ]; then
  cd vvaharness-console
else
  echo "==> Cloning $REPO_URL"
  git clone "$REPO_URL" vvaharness-console
  cd vvaharness-console
fi

echo "==> Updating repo"
git pull --ff-only || echo "warning: git pull failed; continuing with the current checkout" >&2

echo "==> Installing backend (Python venv)"
if [ ! -x .venv/bin/pip ]; then
  PYTHON=$(find_python) || err "python3 >= 3.11 is required (set PYTHON=/path/to/python3.11+ and re-run)"
  "$PYTHON" -m venv .venv
fi
./.venv/bin/pip install -q -e backend

echo "==> Installing frontend (npm)"
(cd frontend && npm install --no-audit --no-fund)

echo "==> Starting backend on http://127.0.0.1:8000"
./.venv/bin/uvicorn backend.app.main:app --port 8000 &
BACKEND_PID=$!

cleanup() { kill "$BACKEND_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

sleep 2
kill -0 "$BACKEND_PID" 2>/dev/null || err "backend failed to start"

echo "==> Starting frontend on http://127.0.0.1:5173 (Ctrl+C stops both)"
(cd frontend && npm run dev -- --host 127.0.0.1)
