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
Phase 5 — Indicator Engine ✅ (EMA, RSI, VWAP, SuperTrend, PCR, Open
Interest Analysis, Trend Direction, Volume Analysis - a pure business
module with zero Kite/FastAPI/SQLAlchemy/HTTP dependency)
Phase 6 — Market Context Engine ✅ (converts IndicatorSnapshot into an
objective, deterministic MarketContext - no signals, no BUY/SELL, no
confidence scores; see "Market Context" below)

## Roadmap

CTO review after Phase 5 split the originally-planned "Signal engine"
phase in two: a deterministic Market Context Engine first, then
Strategy Rules (trade signal generation) on top of it. Renumbered below.

1. Project foundation ✅
2. Core backend architecture — database, SQLAlchemy, DI, repository pattern ✅
3. Zerodha authentication, session and token management ✅ (pending live verification)
4. Market data layer — spot, option chain, historical candles ✅
5. Indicator engine — EMA, RSI, VWAP, SuperTrend, PCR, OI ✅
6. Market Context Engine — objective market description, no signals ✅
7. Strategy Rules — trade signal generation, confidence scoring, risk management
8. Paper trading — position management, P&L, trade journal
9. Analytics — performance dashboard, statistics, reports
10. React dashboard — live market view, signal cards, history, charts
11. Telegram notifications, deployment, production hardening

## Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite, Pandas, ta,
KiteConnect SDK, python-dotenv, Pydantic Settings, Uvicorn

**Frontend:** React, Vite, TypeScript

Note: `Pandas` and `ta` are listed in the original tech stack but are
**not used** - Phase 5's indicator calculators are implemented in plain
Python against `app.market_data.schemas.Candle`, not pandas DataFrames.
At the data volumes involved (a bounded list of candles per calculation,
not bulk historical analysis), plain Python avoids a fairly heavy
dependency for what are otherwise simple formulas, and keeps the module
free of anything beyond pydantic + the standard library. Flagging this
as a deviation from the original stack for visibility, not a silent
substitution - happy to switch to pandas/ta if there's a reason to
prefer them going forward.

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
│   │   ├── trading/
│   │   │   ├── indicators/      # Pure business module - zero Kite/FastAPI/
│   │   │   │   │                # SQLAlchemy/HTTP dependency (see below)
│   │   │   │   ├── ema.py, rsi.py, vwap.py, supertrend.py, volatility.py,
│   │   │   │   │   put_call_ratio.py, open_interest.py,
│   │   │   │   │   trend_direction.py, volume_analysis.py
│   │   │   │   ├── models.py    # IndicatorSnapshot (frozen)
│   │   │   │   └── engine.py    # calculate_indicator_snapshot() - composes all 9
│   │   │   └── context/         # Same purity constraints as indicators/
│   │   │       ├── trend.py, momentum.py, volatility.py, volume_strength.py,
│   │   │       │   market_bias.py, option_chain_bias.py, overall_state.py
│   │   │       ├── models.py    # MarketContext (frozen)
│   │   │       └── engine.py    # build_market_context() - composes all dimensions
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
│   │   ├── market_data/         # Same - a fake MarketDataClient, no real Kite calls
│   │   └── trading/
│   │       ├── indicators/      # Pure math - no fakes/mocks needed at all
│   │       └── context/         # Same - pure classification logic
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

## Indicator Engine

`app/trading/indicators/` calculates EMA, RSI, VWAP, SuperTrend,
Volatility (ATR/ATR%), Put Call Ratio, Open Interest Analysis, Trend
Direction, and Volume Analysis. It generates no trading signals and
contains no trading rules - it only calculates. Confirmed by grep, not
just by design intent: nothing under `app/trading/` imports `app.kite`,
`app.api`, `app.core.database`, `fastapi`, `sqlalchemy`, or
`kiteconnect`; the only `app.*` import anywhere in the package is
`app.market_data.schemas.Candle` (a normalized market data model, per
the brief). Each of the 9 calculators is a standalone module and none
imports another - also confirmed by grep, not asserted. `engine.py` is
the one place that imports all of them, to compose the single immutable
output, `IndicatorSnapshot` (`models.py`).

Two calculators - Put Call Ratio and Open Interest Analysis - take plain
numeric inputs (OI totals, price/OI deltas) rather than a
`app.market_data` schema. Phase 4's `OptionContract` doesn't carry open
interest: it's built on Kite's `ltp()` response, and OI only comes back
from the richer `quote()` call, which Phase 4 doesn't wire up. Rather
than reopen approved Phase 4 code for this, these two calculators accept
whatever numbers they're given; sourcing real OI data is later work.

SuperTrend's expected values are verified by behavior (bullish in a
clear uptrend with the line trailing below price, bearish in a downtrend
with the line above price) rather than an exact hand-computed decimal,
given how many interacting steps its recursive band-flipping algorithm
has - the other eight indicators are checked against exact hand-computed
values.

Volatility (ATR/ATR%) was added while building Phase 6 (Market Context),
not originally part of Phase 5's approved indicator list - the Context
Engine needs a volatility measure and none existed. Computes its own
true-range series rather than importing SuperTrend's private ATR helper,
preserving the "no indicator depends on another" rule at the cost of
duplicating a small amount of math.

## Market Context

`app/trading/context/` converts an `IndicatorSnapshot` into an
objective, deterministic description of the current market: Trend,
Momentum, Volatility, Volume Strength, Market Bias, Option Chain Bias,
Session State, and Overall Market State. It generates no trade signals,
makes no entry decisions, and computes no confidence score or
probability - confirmed by grep for "buy", "sell", "confidence", and
"probability" anywhere in the package (none found), in addition to the
same import-boundary check as the Indicator Engine (clean of
`app.kite`/`app.api`/`app.core.database`/`fastapi`/`sqlalchemy`/
`kiteconnect`).

Two things worth knowing about the inputs:

- **Session State** is not derived from any indicator - it's
  fundamentally about wall-clock time. Rather than force it into
  `IndicatorSnapshot` where it doesn't belong, `build_market_context()`
  takes Phase 4's `MarketSessionStatus` as a second, explicit argument
  alongside the snapshot.
- Every classifier except `overall_state.py` reads only raw
  `IndicatorSnapshot` fields, never another classifier's output -
  `engine.py` (and `overall_state.py`, which composes the *already-computed*
  Trend/Market Bias/Volatility) are the only places that cross-reference.

Two dimensions are deliberately built from *different* indicator pairs
so they say something distinct, not the same fact twice: **Trend**
requires `trend_direction` and SuperTrend to agree; **Market Bias**
requires `trend_direction` and RSI's direction (above/below 50) to
agree. **Option Chain Bias** requires PCR and the Open Interest signal
to agree, using standard PCR interpretation (PCR > 1 skews bullish -
heavy put writing suggests support; PCR < 1 skews bearish - heavy call
writing suggests resistance). `market_bias` and `option_chain_bias`
share one `Bias` enum (`BullishBias`/`BearishBias`/`NeutralBias`) rather
than two near-duplicate ones, since both are the same vocabulary applied
to different data.

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
