# NIFTY Guardian v2

Trade with Discipline. Not Emotion.

A web application that generates high-confidence paper-trading signals for
NIFTY weekly options using live Zerodha Kite data.

**This application is for paper trading only. There is no automated
real-money trading anywhere in this codebase.**

## Status

Phase 1 — Project Foundation ✅
Phase 2 — Core Backend Architecture ✅ (database, SQLAlchemy, dependency
injection, generic repository pattern)
Phase 3 — Zerodha Authentication ✅ code-complete, unit-tested, and the
login redirect verified live; **the actual login exchange has not been
verified against a real Zerodha account** - that needs real
`KITE_API_KEY`/`KITE_API_SECRET` and an interactive browser login only
you can perform. See "Kite Authentication" below.
Phase 4 — Market Data Layer ✅ (spot price, historical candles, option
chain, expiry discovery, instrument lookup, market session validation -
all independent of trading logic, fully unit-tested against a fake Kite
client)

## Roadmap

1. Project foundation ✅
2. Core backend architecture — database, SQLAlchemy, DI, repository pattern ✅
3. Zerodha authentication, session and token management ✅ (pending live verification)
4. Market data layer — spot, option chain, historical candles ✅
5. Indicator engine — EMA, RSI, VWAP, SuperTrend, PCR, OI
6. Signal engine — trading rules, confidence scoring, risk management
7. Paper trading — position management, P&L, trade journal
8. Analytics — performance dashboard, statistics, reports
9. React dashboard — live market view, signal cards, history, charts
10. Telegram notifications, deployment, production hardening

## Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite, Pandas, ta,
KiteConnect SDK, python-dotenv, Pydantic Settings, Uvicorn

**Frontend:** React, Vite, TypeScript

Note: `Pandas` and `ta` aren't installed yet - they arrive in Phase 5
(indicator engine), the first phase that needs them. Everything else
listed above is already in use as of Phase 3.

## Project Structure

```
.
├── .github/workflows/ci.yml     # CI: lint, type-check, test, build
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings, loaded from .env
│   │   │   ├── logging.py       # Centralized logging configuration
│   │   │   ├── database.py      # SQLAlchemy engine/session, get_db DI dependency
│   │   │   ├── repository.py    # Generic Repository[ModelType] base class
│   │   │   └── security.py      # Fernet encryption for secrets at rest
│   │   ├── kite/
│   │   │   ├── client.py        # KiteConnect SDK client factory
│   │   │   ├── models.py        # KiteSession (encrypted access token)
│   │   │   ├── repository.py    # KiteSessionRepository - save/get valid token
│   │   │   └── service.py       # KiteAuthService - login_url / complete_login
│   │   ├── market_data/         # Independent of all trading/business logic
│   │   │   ├── client.py        # MarketDataClient Protocol - the ONLY Kite SDK seam
│   │   │   ├── schemas.py       # Normalized SpotPrice/Candle/Instrument/OptionContract
│   │   │   ├── instrument_lookup.py  # Daily-cached instrument dump + lookups
│   │   │   ├── spot_price.py
│   │   │   ├── candles.py
│   │   │   ├── expiry.py
│   │   │   ├── option_chain.py
│   │   │   └── market_session.py     # Pure time-based, no Kite client needed
│   │   └── api/
│   │       └── routes/
│   │           ├── health.py       # GET /health (includes DB connectivity check)
│   │           ├── kite_auth.py    # GET /auth/kite/login, /auth/kite/callback
│   │           └── market_data.py  # GET /market-data/{session,spot,candles,expiries,option-chain}
│   ├── tests/
│   │   ├── test_health.py
│   │   ├── test_repository.py
│   │   ├── kite/                # Auth tests use a fake Kite client - no
│   │   │                        # real network calls or credentials needed
│   │   └── market_data/         # Same - a fake MarketDataClient, no real Kite calls
│   ├── Dockerfile
│   ├── pyproject.toml           # ruff + mypy + pytest config
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Home page (shows backend connection status)
│   │   ├── main.tsx
│   │   └── env.d.ts             # Typed Vite environment variables
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
├── scripts/
│   ├── dev-backend.sh
│   └── dev-frontend.sh
└── .gitignore
```

## Getting Started

### Backend

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
../scripts/dev-backend.sh
```

The API will be available at `http://localhost:8000`. Check
`http://localhost:8000/health`.

Run tests and code quality checks:

```bash
cd backend
.venv/bin/python -m pytest tests/ -v
.venv/bin/ruff check .
.venv/bin/mypy app tests
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
../scripts/dev-frontend.sh
```

The app will be available at `http://localhost:5173` and will show the
live backend connection status on load.

Run checks:

```bash
cd frontend
npm run lint
npm run format:check
npm run typecheck
npm run build
```

### Development Scripts

- `scripts/dev-backend.sh` — starts the FastAPI backend with auto-reload.
- `scripts/dev-frontend.sh` — starts the Vite dev server.

Both scripts expect a `.env` file to already exist (copy from `.env.example`
in the corresponding directory) and, for the backend, a `.venv` with
dependencies installed.

### Docker

```bash
docker compose up --build
```

Backend on `http://localhost:8000`, frontend on `http://localhost:5173`.
Requires `backend/.env` to exist first. Note: the Docker build itself was
not verified end-to-end in the development sandbox this project was built
in, because that environment's network policy blocks Docker Hub image
pulls — please verify `docker compose up --build` in an environment with
normal registry access before relying on it.

### CI

`.github/workflows/ci.yml` runs on every push and pull request: backend
lint (ruff), type check (mypy), and tests (pytest); frontend lint (oxlint),
format check (prettier), type check (tsc), and build. All steps were run
locally and pass; the workflow itself has not been observed running on
GitHub Actions yet.

## Kite Authentication

1. Register an app in the [Zerodha developer console](https://developers.kite.trade/)
   with redirect URL `http://localhost:8000/auth/kite/callback`, and set
   `KITE_API_KEY`/`KITE_API_SECRET` in `backend/.env`.
2. Generate and set `SECRET_KEY` (required - the app will not start without
   it): `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
3. Visit `http://localhost:8000/auth/kite/login` in a browser, log in with
   your Zerodha credentials, and you'll be redirected back to
   `/auth/kite/callback`, which exchanges the request token for a session
   and stores the access token encrypted in the database.
4. Kite access tokens expire daily - `KiteSessionRepository.get_valid_access_token()`
   treats a session as stale if its login wasn't today (Asia/Kolkata) and
   returns `None`, meaning step 3 needs to be repeated. The authoritative
   check is always the Kite API itself rejecting an actually-expired token
   with `TokenException` - the same-day check is a heuristic, not an exact
   replica of Kite's expiry algorithm.

**This flow is implemented and unit-tested against a fake Kite client, and
the login redirect was verified live (it produces a correct
`kite.zerodha.com` login URL and 503s cleanly if unconfigured), but the
actual login exchange has not been exercised against a real Zerodha
account** - that requires real credentials and an interactive browser
login that only you can perform.

## Market Data

`app/market_data/` obtains, validates, and normalizes market data - spot
price, historical candles, option chain, expiry discovery, instrument
lookup, and market session status. It contains no trading logic, no
indicators, and no signal generation; those arrive in later phases and
will consume this module's output rather than being part of it.

Every Kite SDK call in this module goes through one seam:
`app.market_data.client.MarketDataClient` (a `Protocol`), implemented for
real by `KiteMarketDataClient` and by a `FakeMarketDataClient` in tests -
confirmed by grep that `kiteconnect` is imported nowhere else under
`app/market_data/`, and that nothing in `app/market_data/` imports
`app.kite`. `GET /market-data/session` needs no Kite session at all
(it's pure clock logic); the other endpoints require a valid one from
Phase 3 and return a clean `401` if there isn't one.

Fixed while verifying this phase (a Phase 2/3 gap this phase happened to
surface, not new Phase 4 scope): the app never actually created its
database schema at runtime - `Base.metadata.create_all()` was only ever
called in test fixtures. `main.py` now calls it at startup. This is
adequate for now but doesn't handle migrating an existing schema -
Alembic should replace it before any real deployment.

## Configuration

All configuration is read from environment variables. Nothing is
hardcoded. See `backend/.env.example` and `frontend/.env.example` for the
full list of variables and their defaults.

## Security

Never commit `.env`, API keys, passwords, access tokens, TOTP secrets, or
`kite_token.json`. These are all excluded via the root `.gitignore` from
the very first commit of this project.

Kite access tokens are additionally encrypted at rest in the database
(Fernet, keyed by `SECRET_KEY`) rather than stored in plaintext - see
`app/core/security.py` and `app/kite/repository.py`.

## Engineering Principles

- SOLID principles and clean architecture (config, logging, and routing
  are separated into their own modules from the start).
- Type hints throughout the Python code (mypy strict mode); TypeScript
  throughout the frontend.
- Logging via the standard `logging` module — no `print()` statements.
- Configuration exclusively from environment variables via Pydantic
  Settings.
- Unit-test friendly structure (see `backend/tests/`).
- Automated linting, formatting, and type checking on every change (ruff,
  mypy, oxlint, prettier), enforced in CI.
