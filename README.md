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
Phase 7 — Trading Conditions ✅ (determines whether trading is currently
*permitted* - no BUY/SELL, no confidence score; see "Trading Conditions"
below)
Phase 8 — Strategy Engine ✅ (plugin architecture executing all
registered strategies; one complete strategy - EMA Breakout - no
BUY/SELL decisions, no confidence scoring; see "Strategy Engine" below)
Phase 9 — Risk Engine ✅ (position sizing, stop-loss/target, and four
independent risk-limit gates - evaluated independently of strategy
validity, no approve/reject decision; see "Risk Engine" below)
Phase 10 — Decision Engine ✅ (combines StrategyEvaluation,
TradingConditions, and RiskAssessment into a TradeRecommendation - no
trade execution, no position management, no P&L; see "Decision Engine"
below)

## Roadmap

CTO review after Phase 5 split the originally-planned "Signal engine"
phase in two: a deterministic Market Context Engine first, then
Strategy Rules (trade signal generation) on top of it. CTO review after
Phase 6 inserted a further Trading Conditions layer before Strategy
Rules - permission-to-trade is a separate concern from market
description. CTO review after Phase 7 split "Strategy Rules" itself:
a plugin-based Strategy Engine that runs every registered strategy
first, with choosing between strategies and final BUY/SELL decisions
deferred to later work. CTO review after Phase 8 inserted a Risk Engine
before the final decision layer - risk evaluation (can this be sized
safely, is it within today's limits) is a separate concern from
whether a strategy is technically valid. CTO review after Phase 9
delivered that final decision layer as the Decision Engine - the one
place `StrategyEvaluation.valid`, `RiskAssessment.risk_ok`, and
`TradingConditions.can_trade` are finally combined. Renumbered below.

1. Project foundation ✅
2. Core backend architecture — database, SQLAlchemy, DI, repository pattern ✅
3. Zerodha authentication, session and token management ✅ (pending live verification)
4. Market data layer — spot, option chain, historical candles ✅
5. Indicator engine — EMA, RSI, VWAP, SuperTrend, PCR, OI ✅
6. Market Context Engine — objective market description, no signals ✅
7. Trading Conditions — is trading currently permitted, no signals ✅
8. Strategy Engine — plugin strategies, EMA Breakout, no final BUY/SELL yet ✅
9. Risk Engine — position sizing, stop-loss/target, risk limits, no approve/reject yet ✅
10. Decision Engine — combines strategy/risk/conditions into a TradeRecommendation ✅
11. Paper trading — position management, P&L, trade journal
12. Analytics — performance dashboard, statistics, reports
13. React dashboard — live market view, signal cards, history, charts
14. Telegram notifications, deployment, production hardening

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
│   │   │   ├── context/         # Same purity constraints as indicators/
│   │   │   │   ├── trend.py, momentum.py, volatility.py, volume_strength.py,
│   │   │   │   │   market_bias.py, option_chain_bias.py, overall_state.py
│   │   │   │   ├── models.py    # MarketContext (frozen)
│   │   │   │   └── engine.py    # build_market_context() - composes all dimensions
│   │   │   ├── conditions/      # Same purity constraints again - permission, not signals
│   │   │   │   ├── market_open_filter.py, opening_range_filter.py,
│   │   │   │   │   no_trade_zone_filter.py, session_validation.py,
│   │   │   │   │   expiry_day_filter.py, gap_filter.py, position_guard.py,
│   │   │   │   │   cooldown.py, liquidity.py
│   │   │   │   ├── _time_utils.py  # HH:MM parsing + IST normalization helpers
│   │   │   │   ├── models.py    # TradingConditions (frozen), NoTradeReason
│   │   │   │   └── engine.py    # build_trading_conditions() - composes all evaluators
│   │   │   ├── strategy/        # Same purity constraints again - no BUY/SELL, no scoring
│   │   │   │   ├── base.py      # Strategy Protocol - the plugin interface
│   │   │   │   ├── models.py    # StrategyEvaluation (frozen), StrategyDirection/Strength
│   │   │   │   ├── registry.py  # StrategyRegistry, default_registry()
│   │   │   │   ├── engine.py    # run_strategies() - executes every registered strategy
│   │   │   │   └── ema_breakout.py  # EMABreakoutStrategy - the one built-in strategy
│   │   │   ├── risk/            # Same purity constraints again - no approve/reject
│   │   │   │   ├── position_sizing.py, reward_risk.py, stop_loss.py, target.py,
│   │   │   │   │   daily_loss_limit.py, max_trades_per_day.py,
│   │   │   │   │   capital_exposure.py, max_concurrent_positions.py
│   │   │   │   ├── models.py    # RiskAssessment (frozen), RiskConfig, CapitalState
│   │   │   │   └── engine.py    # build_risk_assessment() - composes all evaluators
│   │   │   └── decision/        # Same purity constraints again - no execution, no P&L
│   │   │       ├── models.py    # TradeRecommendation (frozen), StrategyCandidate
│   │   │       └── engine.py    # build_trade_recommendation() - selects among candidates
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
│   │       ├── context/         # Same - pure classification logic
│   │       ├── conditions/      # Same - pure permission logic
│   │       ├── strategy/        # Same - pure rule evaluation, one stub strategy for engine tests
│   │       ├── risk/            # Same - pure numeric evaluation, no fakes/mocks needed
│   │       └── decision/        # Same - pure selection logic, no fakes/mocks needed
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
├── docs/
│   └── adr/                     # Architecture Decision Records - see docs/adr/README.md
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

`close_price` was added to `IndicatorSnapshot` while building Phase 8
(Strategy Engine) - the EMA Breakout Strategy's "price above/below EMA"
and "price above/below VWAP" checks need the underlying candle close,
which `calculate_indicator_snapshot()` already receives via its
`candles` argument but never previously exposed on the output model.
It is the latest candle's `close`, not a live tick - the same
resolution every other field in the snapshot is already computed at.

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

## Trading Conditions

`app/trading/conditions/` answers one question only: **is trading
currently permitted?** It does not decide BUY/SELL and computes no
confidence score - confirmed by grep for "buy", "sell", "confidence",
and "probability" anywhere in the package (none found), plus the same
import-boundary check as the Indicator Engine and Market Context Engine
(clean of `app.kite`/`app.api`/`app.core.database`/`fastapi`/
`sqlalchemy`/`kiteconnect`). The only cross-package imports anywhere in
the layer are `app.market_data.market_session.MarketSessionStatus` and
`app.trading.context.models.MarketContext` - both already-approved, pure
data types, nothing broker- or framework-specific.

Nine independent evaluators, each a standalone module with no
cross-imports between them (verified by grep, same discipline as the
Indicator Engine):

- **Market open filter** - is the session state `OPEN`.
- **Opening range filter** - blocks the first N minutes after open
  (default 15) to avoid the most volatile part of the session.
- **No-Trade Zone filter** - blocks the final N minutes before close
  (default 15), *or* whenever the Market Context Engine classifies the
  overall market as `VolatileRange`. This is the one evaluator that
  reads `MarketContext` rather than only clock/config values - a
  deliberate design choice, not an oversight, since "is the market too
  choppy to trade" is exactly the kind of condition this layer exists to
  express.
- **Trading session validation** - session must be `OPEN` *and* it must
  be a weekday. There is no exchange holiday calendar wired up anywhere
  in this codebase (flagged since Phase 4) - a holiday that falls on a
  weekday is not caught.
- **Expiry day filter** - whether trading is allowed on an option's own
  expiry day, per configuration. Passes automatically when no expiry
  date is supplied.
- **Gap filter** (framework only) - no live previous-close-vs-open data
  source exists yet, so this only evaluates when a gap percentage is
  actually supplied; passes automatically otherwise.
- **Existing position guard** (interface/stub only) - paper trading
  (a later phase) doesn't exist yet, so callers supply
  `has_open_position` explicitly rather than this querying a real
  position store.
- **Cooldown framework** - blocks new entries for a configured period
  after the last trade closed; passes automatically when no
  `last_trade_closed_at` is supplied, for the same paper-trading-doesn't-
  exist-yet reason as the position guard.
- **Minimum liquidity framework** - requires a contract's volume to meet
  a configured minimum; passes automatically when no volume is supplied,
  since Phase 4's `OptionContract` doesn't carry volume/OI (the same gap
  already flagged for Open Interest in Phase 5).

`engine.py`'s `build_trading_conditions()` composes all nine into the
single immutable `TradingConditions` output (`models.py`). `can_trade` is
`False` if any evaluator fails; `no_trade_reason` reports the *first*
failing condition in a fixed priority order (session/timing gates first,
then position/cooldown, then gap/liquidity), since the field is
singular and can't report every failure at once. `models.py` also
exposes `gap_filter_ok` and `position_guard_ok` alongside the field names
given as examples in the brief (`session_valid`, `opening_range_complete`,
`within_trading_window`, `expiry_allowed`, `liquidity_ok`,
`cooldown_complete`) - the brief's list was explicitly non-exhaustive,
and every evaluator's result should be visible on the output, not
silently folded away.

## Strategy Engine

`app/trading/strategy/` is a plugin architecture: strategies implement
the `Strategy` interface (`base.py` - a `name` attribute and an
`evaluate(snapshot, context, conditions)` method), register themselves
with a `StrategyRegistry` (`registry.py`), and `run_strategies()`
(`engine.py`) simply executes every registered strategy against the
same `IndicatorSnapshot`/`MarketContext`/`TradingConditions` inputs and
returns their evaluations. It does not compare, rank, or choose between
strategies, and it generates no final BUY/SELL decision - both are
explicitly out of scope for this phase. Confirmed by grep, same
discipline as every earlier `app/trading/` package: clean of
`app.kite`/`app.api`/`app.core.database`/`fastapi`/`sqlalchemy`/
`kiteconnect`, and no "buy"/"sell" literal or "confidence"/"probability"
term anywhere in the actual code (the two "BUY/SELL"/"confidence"
matches that do exist are in `ema_breakout.py`'s and `models.py`'s
docstrings, explaining what the design deliberately avoids).

One complete strategy is implemented: **EMA Breakout**, adapted from
the trading rules previously used for NIFTY Guardian's breakout signal
(see the pre-rebuild `debug/signal-runtime` branch's
`indicator_service.py`/`rule_engine.py` - "price > EMA16", "RSI > 55",
"price > VWAP", SuperTrend bullish, combined into a weighted 0-100
confidence score). That original version was long-only and produced a
numeric score; this phase forbids both, so `EMABreakoutStrategy`
instead runs five independent checks - **EMA alignment** (price vs
EMA), **RSI confirmation** (kept at the original bullish threshold of
55, with a symmetric bearish threshold of 45 added so the same rule
recognizes breakouts in either direction), **VWAP confirmation** (price
vs VWAP), **SuperTrend confirmation** (its own bullish/bearish flag),
and **Trend agreement** (the Market Context Engine's own `Trend`
classification, corroborating the four indicator-level checks against
the broader market description) - then:

- Reports `direction` as whichever side (Long/Short) has more agreeing
  checks, or `None` on a tie.
- Reports `strength` as a categorical read of how many checks agree
  (Strong = 5/5, Moderate = 4/5, Weak = 3 or fewer) - not a numeric
  percentage.
- Sets `valid=True` only when at least 4 of the 5 checks agree *and*
  `TradingConditions.can_trade` is `True` - a breakout needs strong
  alignment, not a bare majority, and permission to trade is a hard
  gate independent of how well the technicals line up.
- Still reports the technical `direction`/`strength` even when
  `TradingConditions.can_trade` is `False` (with a warning citing
  `no_trade_reason`), so the evaluation stays informative about what
  the strategy sees rather than going silent - only `valid` reflects
  that it isn't actionable.

## Risk Engine

`app/trading/risk/` evaluates trade risk **independently of strategy
validity** - it does not approve or reject a trade, only whether it
would be within risk limits if taken. `build_risk_assessment()`
(`engine.py`) composes eight independent evaluators into one
`RiskAssessment`: position sizing, stop-loss, target, and reward/risk
are always-computed values; daily loss limit, max trades per day,
capital exposure, and max concurrent positions are risk-limit gates.
`risk_ok` reflects only the four gates (plus a minimum-viable-position
check) - it deliberately ignores `StrategyEvaluation.valid` entirely,
per this phase's explicit requirement. Confirmed by grep, same
discipline as every earlier `app/trading/` package: clean of
`app.kite`/`app.api`/`app.core.database`/`fastapi`/`sqlalchemy`/
`kiteconnect`; the only cross-package import anywhere in the layer is
`app.trading.strategy.models` (`StrategyDirection`/`StrategyEvaluation`,
both already-approved, pure types).

Two configuration inputs are deliberately separate models:
`RiskConfig` holds the trading-rule thresholds an operator sets once
(risk-per-trade percentage, ATR multipliers, daily loss limit, ...);
`CapitalState` holds the account's constantly-changing numbers
(capital deployed, trades already taken today, ...). Neither has
defaults - both must come from the caller, consistent with "nothing
hardcoded" - so every unit test constructs them explicitly.

Two inputs needed adding beyond the phase's stated four
(`StrategyEvaluation`, `TradingConditions`, Configuration, Capital
settings), both flagged the same way earlier gaps were: **`entry_price`**
and **`atr`** are required, explicit parameters, because none of
position sizing, stop-loss, target, reward/risk, or capital exposure
can be computed without a price to enter at and a volatility measure to
size the stop distance from, and no listed input carries either.
`atr` is passed as a bare `float` (sourced from
`IndicatorSnapshot.atr`) rather than the whole snapshot, so this
package's only real dependency stays `app.trading.strategy`.
Stop-loss/target are ATR-multiplier-based, not a flat percentage of
price - the distance scales with current volatility rather than an
arbitrary fixed percentage.

**`TradingConditions` is intentionally not a parameter** of
`build_risk_assessment()`, even though the phase brief lists it as an
input: none of the eight risk evaluators has a legitimate use for
session/timing state, and gating `risk_ok` on it would reintroduce the
same "approve/reject" behavior this phase explicitly rules out for
strategy validity - the same principle extends to trading permission.
The layer that eventually combines `StrategyEvaluation`,
`TradingConditions`, and `RiskAssessment` into an actual go/no-go
decision is later work (the "Final decision layer" on the roadmap).

`StrategyEvaluation` itself is used for exactly one thing: its
`direction`, to place stop-loss and target on the correct side of
`entry_price` (below/above for Long/Short, collapsed to `entry_price`
itself with `position_size=0` when direction is `None` - mirroring how
the pre-rebuild `debug/signal-runtime` branch's `risk_engine.py`
handled its own "no signal" case).

## Decision Engine

`app/trading/decision/` is the one layer allowed to combine
`StrategyEvaluation`, `TradingConditions`, and `RiskAssessment`
together into a single `TradeRecommendation` (`models.py`/`engine.py`).
It does not execute trades, maintain positions, or update P&L - it only
determines whether a recommendation exists and explains why. Confirmed
by grep, same discipline as every earlier `app/trading/` package: clean
of `app.kite`/`app.api`/`app.core.database`/`fastapi`/`sqlalchemy`/
`kiteconnect`, and the only cross-package imports anywhere in the layer
are `app.trading.strategy.models`, `app.trading.risk.models`, and
`app.trading.conditions.models` - the three inputs the phase specifies,
nothing else.

`build_trade_recommendation()` takes a `list[StrategyCandidate]` (each
pairing one strategy's `StrategyEvaluation` with the `RiskAssessment`
computed for its direction - Phase 8 registers multiple strategies and
explicitly deferred "choosing between strategies" to this phase, and
Phase 9's `RiskAssessment` is inherently per-strategy since it needs a
direction) plus the shared `TradingConditions`:

- A candidate **qualifies** only when both its `StrategyEvaluation.valid`
  and its `RiskAssessment.risk_ok` are `True` - the two independent
  gates from Phases 8 and 9 finally meet here, and only here.
- Among qualifying candidates, the strongest wins (`Strong` over
  `Moderate` - `Weak` never qualifies, since Phase 8's `valid` already
  requires at least `Moderate`), tied-broken by the higher
  `reward_risk_ratio`, then by registration order - fully deterministic,
  no randomness anywhere in the selection.
- If no candidate qualifies (including an empty candidate list),
  `recommended=False`, `direction=None`, `selected_strategy=None`,
  `recommendation_strength=None`, `risk_summary=None`, and `warnings`
  explains which candidates failed and why (strategy not valid, or risk
  not ok with its specific `rejection_reasons`).
- Even when a candidate qualifies, `TradingConditions.can_trade` is a
  final, separate gate on `recommended` itself - mirroring the
  transparency pattern from Phases 7-9, the technical read (`direction`,
  `selected_strategy`, `risk_summary`) is still reported when
  `can_trade` is `False`, with a warning citing `no_trade_reason`; only
  `recommended` reflects that it isn't actionable.

`risk_summary` is the winning candidate's own `RiskAssessment`, reused
directly rather than duplicated into a new summary type - consistent
with reusing `Bias` across `market_bias`/`option_chain_bias` in Phase 6
and `MarketSessionStatus` across `market_data`/`context` in Phase 4.

## Architecture Decision Records

`docs/adr/` records the major architectural decisions made across this
rebuild - layered domain architecture, no BUY/SELL/confidence scoring
below the Decision Engine, broker isolation via Protocol seams, the
strategy plugin architecture, risk's independence from strategy
validity, immutable frozen models, and the policy for gap-fixing
already-approved phases. See `docs/adr/README.md` for the index.

## System Architecture Document

`docs/SYSTEM_ARCHITECTURE.md` is the complete technical architecture
reference: overview and guiding principles, the high-level pipeline
diagram, every package's responsibility, each layer's inputs/outputs/
forbidden responsibilities, the full dependency graph, an end-to-end
data-flow walkthrough, extension points (new strategy/broker/indicator/
risk rule), the testing strategy, an ADR summary, and the future
roadmap.

## Demo Pipeline Script

`scripts/demo_pipeline.py` runs the entire pipeline end to end - Sample
Market Data → `IndicatorSnapshot` → `MarketContext` →
`TradingConditions` → `StrategyEvaluation` → `RiskAssessment` →
`TradeRecommendation` - against deterministic hand-built sample data.
It requires no Zerodha credentials, no network access, and no FastAPI
server; run it with:

```bash
python3 scripts/demo_pipeline.py
```

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
