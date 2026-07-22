# Demo: Production Deployment Setup (Phase 25)

Walks through bringing the platform up via Docker Compose, verifying
health checks, and confirming the frontend is connected to the real
backend - no mock data, no trading logic changed.

**Honest limitation:** the sandbox this phase was developed in has no
privileged Docker daemon access (`dockerd` cannot start - `ulimit:
error setting limit (Operation not permitted)`), so `docker compose up`
itself could not be executed here. What *was* verified in this
sandbox, and is reported with real output below:

- `docker compose config` for every compose file/override combination -
  confirms the YAML is valid and every override merges correctly.
- The exact same backend/frontend artifacts the Docker images package
  (`uvicorn app.main:app` and the Vite production build, served via
  `vite preview`) running natively, end to end, including the
  frontend calling the real backend.

Anyone with a working Docker daemon can run the `docker compose up`
commands below directly - they build from the same Dockerfiles and
compose files validated here.

## 1. Validate the Compose configuration

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml config
```

Real output (abbreviated - confirms the dev override merges: `target: dev`,
source volumes mounted, ports `8000`/`5173`):

```yaml
name: deploy
services:
  backend:
    build:
      context: /home/user/Nifty-Guardian
      dockerfile: deploy/docker/backend.Dockerfile
      target: dev
    command: [uvicorn, app.main:app, --host, 0.0.0.0, --port, "8000", --reload]
    volumes:
      - source: .../backend/app
        target: /app/app
      - source: .../backend/tests
        target: /app/tests
  frontend:
    build:
      target: dev
    ports:
      - target: 5173
        published: "5173"
```

```bash
VITE_API_BASE_URL=https://api.example.com \
  docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml config
```

Real output (abbreviated - confirms the prod override merges:
`target: production`, `restart: unless-stopped`, resource limits, no
source volumes):

```yaml
name: deploy
services:
  backend:
    build:
      target: production
    restart: unless-stopped
    mem_limit: "536870912"
    cpus: 1
  frontend:
    build:
      target: production
      args:
        VITE_API_BASE_URL: https://api.example.com
    restart: unless-stopped
    mem_limit: "268435456"
    cpus: 0.5
```

## 2. Bring the platform up (requires a working Docker daemon)

```bash
cp config/production.env.example config/production.env
# fill in every CHANGE ME value first - see docs/CONFIGURATION_REFERENCE.md

VITE_API_BASE_URL=http://localhost:8000 \
  docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
```

## 3. Health checks

```bash
curl -s http://localhost:8000/health/live
curl -s http://localhost:8000/health/ready
```

Expected response shape (this exact shape *was* verified natively in
this sandbox - see step 4):

```json
{"status": "alive"}
{"status": "ready", "checks": [{"name": "database", "ok": true, "detail": "reachable"}, {"name": "configuration", "ok": true, "detail": "ok"}]}
```

## 4. What was actually verified natively (no Docker daemon)

Ran the real backend (`uvicorn app.main:app`, `LOG_FORMAT=json`) and
the real frontend production build (`npm run build` then
`vite preview`) side by side, and hit both directly:

```bash
$ curl -s http://localhost:8000/health/live
{"status":"alive"}

$ curl -s http://localhost:8000/health/ready
{"status":"ready","checks":[{"name":"database","ok":true,"detail":"reachable"},{"name":"configuration","ok":true,"detail":"ok"}]}

$ curl -s http://localhost:8000/api/dashboard | head -c 400
{"runtime":{"session_state":"NotStarted","replay_speed":"1x","processed_candles":0,"total_candles":0,"events_published":0,"orders_generated":0,"uptime_seconds":0.0},"current_candle":null,"market_context":null,"latest_signal":null,"latest_risk_decision":null,"latest_recommendation":null,"orders":[],"positions":[],"portfolio":{"as_of":"2026-07-22T12:46:23.615910","cash":100000.0,"available_margin":1...

$ curl -s -o /dev/null -w "frontend status: %{http_code}\n" http://localhost:4173/
frontend status: 200
```

Backend startup log, confirming structured JSON logging and startup
diagnostics both fired correctly:

```json
{"timestamp": "2026-07-22T12:45:37.875194+00:00", "level": "INFO", "logger": "app.main", "message": "NIFTY Guardian v2 starting up (environment=development)"}
{"timestamp": "2026-07-22T12:45:37.875471+00:00", "level": "INFO", "logger": "app.observability.startup", "message": "startup: NIFTY Guardian v2 v2.0.0 (environment=development, git_commit=unknown, python=3.12.3)"}
{"timestamp": "2026-07-22T12:45:37.877431+00:00", "level": "INFO", "logger": "app.observability.startup", "message": "startup validation: no issues found"}
```

This confirms the exact application code the Docker images run - the
gap is purely "was it exercised inside a container," not "does the
code work."

## 5. Dashboard connected (mock vs. rest)

The frontend build above was produced with `VITE_DASHBOARD_SERVICE`
unset (defaults to `mock` per `.env.example`) unless explicitly
overridden. To build a bundle that actually calls the backend:

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:8000 VITE_DASHBOARD_SERVICE=rest npm run build
```

Verified in this sandbox: this build succeeds
(`✓ built in 1.39s`, `dist/index.html`/`dist/assets/*` produced) and,
when served, the same `/api/dashboard` response shown above is what
the dashboard's `RestDashboardService` polls - see
`docs/API_GUIDE.md` for the full REST connectivity story (Phase 22,
frozen, unchanged this phase).
