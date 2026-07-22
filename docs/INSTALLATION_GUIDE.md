# NIFTY Guardian — Installation Guide

This guide covers every supported way to run NIFTY Guardian v2: local
development without containers, local development with Docker, and a
production-style deployment with Docker Compose. It does not cover
Live Trading Mode setup specifically - see `docs/LIVE_TRADING_GUIDE.md`
for that.

## Prerequisites

| Tool | Version | Needed for |
|---|---|---|
| Python | 3.12 | Backend, without containers |
| Node.js | 22 | Frontend, without containers |
| Docker | any recent | Containerized dev/prod |
| Docker Compose | v2 (the `docker compose` plugin, not `docker-compose`) | Containerized dev/prod |

## Option 1: Local development, no containers

This is the fastest inner loop for day-to-day backend/frontend work.

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # edit SECRET_KEY at minimum - see docs/SECURITY.md
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Verify:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

Open `http://localhost:5173` for the dashboard.

## Option 2: Local development with Docker

Uses `deploy/docker-compose.dev.yml` - hot-reloading backend, Vite dev
server for the frontend, source mounted as volumes.

```bash
cp config/development.env.example config/development.env
# edit config/development.env - the packaged SECRET_KEY is a published
# dev-only value, safe for this file only; see docs/SECURITY.md

docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml up --build
```

Backend: `http://localhost:8000`. Frontend (Vite dev server, hot
reload): `http://localhost:5173`.

## Option 3: Production-style deployment with Docker

Uses `deploy/docker-compose.prod.yml` - production Dockerfile targets,
a hardened nginx config for the frontend, restart policies, resource
limits, no source volumes.

```bash
cp config/production.env.example config/production.env
# fill in EVERY value marked CHANGE ME - see docs/CONFIGURATION_REFERENCE.md
# and docs/SECURITY.md before proceeding

VITE_API_BASE_URL=https://your-domain.example.com \
  docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
```

Backend: port 8000. Frontend (nginx serving the production build):
port 80.

Verify:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost/   # frontend
```

See `scripts/demo_production_setup.md` for a full walkthrough
including expected output at each step, and
`docs/RELEASE_CHECKLIST.md` before treating a deployment as
production-ready.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Backend container exits immediately | `SECRET_KEY` not set - `Settings` has no default and refuses to start without it |
| `/health/ready` returns 503 | Check the `checks` array in the response - either the database or `app.observability.startup.validate_startup()` found a configuration error |
| Frontend shows no data | `VITE_API_BASE_URL`/`VITE_DASHBOARD_SERVICE` not set correctly at *build* time - Vite bakes these in, so changing `.env` requires a rebuild, not just a restart |
| `docker compose config` fails with "env file not found" | You skipped copying `config/*.env.example` to `config/*.env` |
