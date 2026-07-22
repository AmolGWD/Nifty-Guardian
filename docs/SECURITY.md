# NIFTY Guardian — Security

Secret management, credential loading, and environment validation for
this platform. This is not a general security policy document - it
covers exactly the mechanisms this codebase implements.

## Secret management

- **Never commit secrets.** `.gitignore` excludes `.env`/`.env.*`
  (everywhere in the repo) and `config/*.env` (Phase 25's environment
  files) - only the `*.env.example` variants are tracked, and those
  contain placeholders or clearly-labeled dev-only values, never real
  credentials.
- Every `*.env.example` file documents what belongs in the real,
  untracked copy - see `docs/CONFIGURATION_REFERENCE.md` for the full
  variable-by-variable reference.
- In CI (`.github/workflows/backend.yml`), `SECRET_KEY` is a published,
  fixed test-only value - not a real secret, never reused outside CI.
- In a real production deployment, prefer injecting `config/production.env`'s
  contents from a secrets manager (your cloud provider's, Vault, etc.)
  at deploy time rather than storing it as a plain file on a host -
  this repository does not implement that integration itself, since it
  varies by deployment target.

## Credential loading

Every credential in this platform loads from environment variables via
Pydantic Settings, never hardcoded, never read from a config file
checked into version control:

- `app.core.config.Settings` - `SECRET_KEY`, `KITE_API_KEY`/`KITE_API_SECRET`.
- `app.brokers.authentication.ZerodhaCredentials` - `ZERODHA_API_KEY`/
  `ZERODHA_API_SECRET`/`ZERODHA_ACCESS_TOKEN`/`ZERODHA_BASE_URL`,
  independently of `app.kite`'s OAuth flow (see
  `docs/ZERODHA_ADAPTER_GUIDE.md`).
- Kite access tokens obtained through the OAuth login flow
  (`app.kite`) are encrypted at rest using Fernet, keyed by
  `SECRET_KEY` - see `app/core/security.py` and
  `app/kite/repository.py`. `ZERODHA_ACCESS_TOKEN` (the Broker
  Adapter's own credential) is supplied directly via environment
  variable and is not additionally stored anywhere by this platform.
- `SECRET_KEY` has no default - `Settings()` raises immediately at
  startup rather than silently running with a shared, guessable key.

## Environment validation

`app.observability.startup.validate_startup()` (Phase 25) inspects
already-loaded settings at startup and surfaces (via `/health/ready`
and startup logs) issues that would otherwise only be discovered when
something actually goes wrong:

- An unrecognized `ENVIRONMENT` value.
- `LOG_LEVEL=DEBUG` in production (excessive detail in logs).
- A `localhost` origin still present in `CORS_ORIGINS` in production.
- A `SECRET_KEY` shorter than expected for a generated Fernet key.
- `LIVE_MODE=true` without both `ZERODHA_API_KEY` and
  `ZERODHA_ACCESS_TOKEN` set.

None of these checks mutate configuration - they only report what they
find. `/health/ready` returns HTTP 503 if any check (including this
one) fails, so a misconfigured production deployment fails its
readiness probe rather than silently serving traffic.

## Network/transport

- CORS is explicit and configured via `CORS_ORIGINS` - never `*` in
  production (flagged, though not currently hard-blocked, by startup
  validation if left as `localhost`).
- This platform does not terminate TLS itself - place it behind a
  reverse proxy or load balancer that does, in any real deployment.
  `deploy/nginx/production.conf` serves plain HTTP on port 80 inside
  the container; TLS termination is out of scope for this phase.

## Reporting a vulnerability

This is a personal/internal project, not a public product - report any
concern directly to the maintainer rather than through a public issue.
