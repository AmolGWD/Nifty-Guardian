# NIFTY Guardian — Operations Runbook

Day-to-day operational procedures for a running deployment. See
`docs/INCIDENT_RESPONSE.md` for what to do when something is actually
broken, and `docs/LIVE_TRADING_GUIDE.md` for Live Trading Mode-specific
safety procedures.

## Starting and stopping

```bash
# Start (production)
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d

# Stop
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml down

# Restart just the backend
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml restart backend
```

`restart: unless-stopped` (set in `docker-compose.prod.yml`) means both
containers restart automatically after a host reboot or a crash - an
explicit `down` is required to actually stop them.

## Monitoring

| What | How |
|---|---|
| Is the backend process alive at all | `GET /health/live` - always 200 if the process can respond, never checks the database |
| Is the backend ready to serve real traffic | `GET /health/ready` - checks database connectivity and configuration validity; 503 if either fails |
| App version/environment/uptime | `GET /health/metadata` |
| Basic request counters/latency | `GET /health/metrics` |
| Original service-status endpoint (Phase 1, unchanged) | `GET /health` |
| Logs | `docker compose logs -f backend` / `docker compose logs -f frontend`. In production (`LOG_FORMAT=json`), each line is one JSON object - pipe through `jq` for readability: `docker compose logs -f backend \| jq -R 'fromjson? // .'` |

A container orchestrator (Docker's own `HEALTHCHECK`, Kubernetes
liveness/readiness probes, a load balancer) should point at
`/health/live` for liveness and `/health/ready` for readiness -
never the other way around, since a database hiccup should not cause
an orchestrator to kill and restart an otherwise-healthy process.

## Common tasks

**Rotating the Zerodha access token.** `ZERODHA_ACCESS_TOKEN` expires
daily and Kite Connect has no refresh mechanism (see
`docs/ZERODHA_ADAPTER_GUIDE.md`). Each trading day: complete the Kite
login flow, obtain a fresh access token, update
`config/production.env`, then restart the backend so it picks up the
new value:

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d --force-recreate backend
```

**Viewing recent safety decisions (Live Trading Mode).**
`SafetyManager.decisions` (in-process, per Phase 24) is not currently
exposed over HTTP - inspect it via the structured logs
(`logger.warning`/`logger.info` lines tagged `SafetyManager[...]`)
until a dedicated endpoint exists.

**Checking for stale heartbeats.** Same caveat - `HeartbeatMonitor`
state is in-process only this phase; watch for `heartbeat` log lines,
or extend `/health/ready` with an additional check in a later phase.

**Rebuilding after a config change.** Any change to `config/production.env`
requires a container recreate (`--force-recreate`) to take effect -
environment variables are read once, at process startup. Any change to
a `VITE_*` variable requires a full image rebuild (`--build`), since
Vite bakes these into the static bundle at build time.

## Backup

| What | Where | How |
|---|---|---|
| Configuration | `config/*.env` (gitignored, never in version control) | Store in a secrets manager or an encrypted vault, not a plain file copy - see `docs/SECURITY.md` |
| Application database | `DATABASE_URL` target (default: a SQLite file under `backend/data/`) | Stop the backend, copy the `.db` file, restart. For a real production deployment, replace SQLite with a server database that supports online backups (see `docs/SYSTEM_ARCHITECTURE.md`'s future-work notes) |
| Logs | stdout, captured by Docker/your log aggregator | Configure your log driver (e.g. `json-file` with rotation, or ship to an external aggregator) - this repository does not implement log shipping itself |
| Historical market data | `backend/data/` (CSV imports via `app.data`, Phase 13) | Back up alongside the application database; re-importable from source if lost |

## Recovery process

1. Stop the affected service(s): `docker compose ... down`.
2. Restore configuration from your secrets manager into `config/*.env`.
3. Restore the database file (if applicable) to the path `DATABASE_URL` points at.
4. Bring the platform back up: `docker compose ... up -d --build`.
5. Verify: `GET /health/ready` returns `200` with every check `ok: true`.
6. If Live Trading Mode was active before the incident, do **not**
   assume any in-flight order state - check
   `OrderExecutor.last_known_status()` (or your broker's own order
   book) before resuming trading; reconnect deliberately never replays
   orders (see `docs/LIVE_TRADING_GUIDE.md`).

## Scaling notes (honest limitations)

This platform is currently single-instance by design - SQLite (the
default database), the in-process `MetricsRegistry`/`HeartbeatMonitor`,
and `RuntimeEngine`'s in-memory state all assume exactly one running
backend process. Running multiple replicas behind a load balancer
would require: a shared database (Postgres/MySQL), a shared metrics
backend (Prometheus), and moving `RuntimeEngine`/`LiveSession` state out
of process memory - none of that is implemented in this phase.
