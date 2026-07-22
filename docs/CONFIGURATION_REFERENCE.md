# NIFTY Guardian — Configuration Reference

Every environment variable this platform reads, grouped by owning
module. All configuration is environment-driven - nothing is
hardcoded per environment. See `config/*.env.example` for
copy-and-fill starting points per environment, and
`docs/SECURITY.md` for secret management guidance.

## Core application (`app.core.config.Settings`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `APP_NAME` | string | `NIFTY Guardian v2` | Displayed in `/health` and `/health/metadata` |
| `ENVIRONMENT` | string | `development` | One of `development`/`staging`/`production` - anything else produces a startup warning |
| `LOG_LEVEL` | string | `INFO` | One of `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL` |
| `LOG_FORMAT` | `text`\|`json` | `text` | `json` emits structured, one-object-per-line logs (`app.observability.logging`); use `json` in staging/production |
| `HOST` | string | `0.0.0.0` | Bind address (mainly relevant outside Docker) |
| `PORT` | int | `8000` | Bind port |
| `CORS_ORIGINS` | comma-separated string | `http://localhost:5173` | Allowed browser origins; a `localhost` value in production produces a startup warning |
| `DATABASE_URL` | string | local SQLite file | SQLAlchemy connection string |
| `SECRET_KEY` | string | **none - required** | Fernet key encrypting secrets (e.g. Kite tokens) at rest. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `KITE_API_KEY` | string | `""` | Kite Connect OAuth login flow (`app.kite`) - a human browser login, unrelated to the Zerodha Broker Adapter below |
| `KITE_API_SECRET` | string | `""` | Same as above |
| `MARKET_OPEN` | `HH:MM` | `09:15` | NSE session start |
| `MARKET_CLOSE` | `HH:MM` | `15:30` | NSE session end |

## Zerodha Broker Adapter (`app.brokers.authentication.ZerodhaCredentials`, `ZERODHA_` prefix)

Deliberately independent of `KITE_API_KEY`/`KITE_API_SECRET` above -
these drive automated broker connectivity via an already-generated
access token, not an interactive login. See
`docs/ZERODHA_ADAPTER_GUIDE.md`.

| Variable | Type | Default | Description |
|---|---|---|---|
| `ZERODHA_API_KEY` | string | `""` | Kite Connect app API key |
| `ZERODHA_API_SECRET` | string | `""` | Kite Connect app API secret |
| `ZERODHA_ACCESS_TOKEN` | string | `""` | Today's already-generated access token - expires daily, no refresh mechanism |
| `ZERODHA_BASE_URL` | string | `None` | Override the Kite Connect API base URL (rarely needed) |
| `ZERODHA_REFRESH_TOKEN` | string | `None` | Honestly documented as unused - Kite Connect has no refresh-token concept; present only because an earlier CTO brief named it |

All three of `ZERODHA_API_KEY`/`ZERODHA_API_SECRET`/`ZERODHA_ACCESS_TOKEN`
are required together the moment anything constructs
`ZerodhaCredentials` - leave all three blank if you aren't using the
Zerodha Broker Adapter at all.

## Live Trading Mode (`app.live.models.LiveConfig`)

See `docs/LIVE_TRADING_GUIDE.md` for the full safety philosophy behind
each of these.

| Variable | Type | Default | Description |
|---|---|---|---|
| `LIVE_MODE` | bool | `false` | Master switch - `false` is the only safe default |
| `MAX_DAILY_LOSS` | float | `10000.0` | Realized-loss cap per day |
| `MAX_OPEN_POSITIONS` | int | `1` | Concurrent open positions cap |
| `MAX_ORDERS_PER_DAY` | int | `10` | Order-count cap per day |
| `HEARTBEAT_INTERVAL_SECONDS` | float | `5.0` | Seconds before a component is considered stale. **Note:** the field is `heartbeat_interval_seconds`, so this is the actual working variable name - the original Phase 24 brief referred to it as `HEARTBEAT_INTERVAL`, which pydantic-settings does not read |
| `RECONNECT_LIMIT` | int | `5` | Maximum reconnect attempts before giving up |
| `TRADING_START` | `HH:MM` | `09:15` | Trading-hours gate start |
| `TRADING_END` | `HH:MM` | `15:30` | Trading-hours gate end |

If `LIVE_MODE=true`, `app.observability.startup.validate_startup()`
raises a startup error (surfaced at `/health/ready`) unless
`ZERODHA_API_KEY`/`ZERODHA_ACCESS_TOKEN` are also both set.

## Deployment metadata (`app.observability.diagnostics`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `APP_VERSION` | string | `2.0.0` | Reported by `/health/metadata`; set as a build arg/env var by CI if you want it to track a release tag |
| `GIT_COMMIT` | string | `unknown` | Reported by `/health/metadata`; set by CI to the commit SHA that produced the image |

## Frontend (Vite - read at **build** time, not runtime)

| Variable | Type | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | string | `http://localhost:8000` | Backend base URL the dashboard calls |
| `VITE_DASHBOARD_SERVICE` | `mock`\|`rest` | `mock` | Which `DashboardService` implementation to use - `mock` needs no backend |
| `VITE_DASHBOARD_POLLING_INTERVAL_MS` | int | `1000` | How often the REST service polls `GET /api/dashboard` |
| `VITE_API_TIMEOUT_MS` | int | `5000` | Per-request timeout before the REST service treats it as failed |
| `VITE_DEFAULT_REPLAY_SPEED` | `1x`\|`2x`\|`5x`\|`10x`\|`Unlimited` | `1x` | Default replay speed sent with `POST /api/runtime/replay` |

Because Vite bakes these into the static build, changing any of them
requires rebuilding the frontend image/bundle - restarting the
container alone has no effect.

## Where each environment's file lives

| Environment | Example (tracked) | Real file (gitignored) |
|---|---|---|
| Development | `config/development.env.example` | `config/development.env` |
| Staging | `config/staging.env.example` | `config/staging.env` |
| Production | `config/production.env.example` | `config/production.env` |

`backend/.env.example`/`frontend/.env.example` remain the quick-start
files for Option 1 in `docs/INSTALLATION_GUIDE.md` (no containers);
`config/*.env.example` are the ones the Docker Compose files in
`deploy/` actually read.
