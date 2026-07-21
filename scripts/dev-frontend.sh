#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../frontend"

if [ ! -f .env ]; then
  echo "No .env found. Copy .env.example to .env first." >&2
  exit 1
fi

exec npm run dev
