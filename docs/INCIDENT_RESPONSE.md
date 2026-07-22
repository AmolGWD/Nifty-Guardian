# NIFTY Guardian — Incident Response

How to respond when something is actually broken, as opposed to
routine operations (`docs/OPERATIONS_RUNBOOK.md`).

## Severity levels

| Level | Definition | Example |
|---|---|---|
| **SEV-1** | Live Trading Mode is active and behaving unsafely, or real money is at risk | A safety gate isn't being enforced; an order was placed unexpectedly |
| **SEV-2** | The platform is down or unreachable | Backend/frontend container crash-looping; `/health/ready` failing platform-wide |
| **SEV-3** | Degraded but functional | A single stale heartbeat; elevated latency; one failed broker call retried successfully |
| **SEV-4** | Cosmetic or non-urgent | A log message misformatted; a dashboard panel showing stale-but-not-wrong data |

## First response, any severity

1. Check `GET /health/ready` - identifies whether the database or
   configuration is the proximate cause.
2. Check `GET /health/metadata` - confirms which version/environment
   is actually running (rules out "wrong deployment" as the cause).
3. Check logs (`docker compose logs -f backend`) for the request ID
   (`X-Request-ID` header) of the affected request, if known -
   `app.observability.logging` attaches it to every log line for that
   request.

## SEV-1: Live Trading Mode is behaving unsafely

**This takes priority over everything else in this document.**

1. **Engage the kill switch or emergency stop immediately.**
   `LiveSession.emergency_stop(reason)` is reachable from any
   non-terminal session state and always disconnects the market feed -
   see `docs/LIVE_TRADING_GUIDE.md`. If no operator tooling exposes
   this yet, stop the backend process entirely
   (`docker compose ... stop backend`) as the blunter equivalent.
2. **Do not restart with `LIVE_MODE=true` until the root cause is
   understood.** Restart with `LIVE_MODE=false` if you need the
   platform back up for any other reason in the meantime.
3. **Check `OrderExecutor.last_known_status()` for every order placed
   in the incident window** - reconnect and restart never
   automatically replay orders, so this is the only record of what
   was actually submitted to the broker. Cross-check against the
   broker's own order book directly (Kite's own dashboard/API) - never
   trust only this platform's view during a live incident.
4. Preserve logs from the incident window before any restart clears
   in-memory state (`SafetyManager.decisions`, `HeartbeatMonitor`
   snapshots) that isn't persisted anywhere yet.
5. Once safe, follow the postmortem process below before re-enabling
   `LIVE_MODE`.

## SEV-2: Platform down

1. `docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml ps`
   - identify which container(s) are unhealthy/exited.
2. `docker compose ... logs backend` (or `frontend`) - the last lines
   before exit are almost always the cause. Common causes:
   - `SECRET_KEY` missing/invalid → `Settings()` fails at import time,
     container exits immediately.
   - Database file path unwritable → check volume/permissions.
   - Port already in use on the host.
3. Fix the underlying cause, then:
   `docker compose ... up -d --force-recreate <service>`.
4. Confirm recovery: `GET /health/ready` returns `200`.

## SEV-3: Degraded

1. Check `GET /health/metrics` for elevated latency
   (`http_request_duration_seconds{path=...}` gauges) or an unusual
   counter value.
2. Check `GET /health/ready`'s `checks` array - a `not_ready` status
   with `ok: false` on a specific check narrows the cause immediately.
3. If the cause is a single stale heartbeat component, see
   `docs/LIVE_TRADING_GUIDE.md`'s Reconnect section - the platform is
   designed to recover on its own within `RECONNECT_LIMIT` attempts;
   only intervene manually if it doesn't.

## SEV-4: Cosmetic

Log and fix in the normal development cycle - no incident procedure
needed.

## Postmortem template

For any SEV-1 or SEV-2 incident:

```
## Incident: <short title>
Date/time (with timezone):
Severity:
Detected by: (health check / user report / log alert)
Duration:

### Timeline
- HH:MM - ...

### Root cause


### Impact
(Was Live Trading Mode active? Was any real order affected?)

### Resolution


### Follow-up actions
- [ ] ...
```
