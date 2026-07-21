#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"

if [ ! -d .venv ]; then
  echo "No .venv found. Create one with: python3.12 -m venv .venv" >&2
  exit 1
fi

if [ ! -f .env ]; then
  echo "No .env found. Copy .env.example to .env first." >&2
  exit 1
fi

exec .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
