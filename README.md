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
Phase 10.5 — Documentation & Validation ✅ (`docs/SYSTEM_ARCHITECTURE.md`,
`scripts/demo_pipeline.py` - a full-architecture freeze point before
Paper Trading; no domain changes)
Phase 11 — Historical Backtesting ✅ (replays historical candles through
the existing pipeline unchanged - no duplicated indicator/strategy/risk
logic; see "Historical Backtesting" below)
Phase 12 — Backtesting Analytics ✅ (CAGR, Sortino/Calmar/Recovery
Factor, yearly/monthly breakdowns, market regime and time-of-day
analysis, trade distribution, streak/drawdown detail, ASCII charts -
analyzes a completed BacktestResult, executes nothing; see "Backtesting
Analytics" below)
Phase 13 — Historical Data Platform ✅ (`app/data/` - import,
validation, in-memory repository/cache, and a provider interface for
historical OHLCV data; CSV implemented, Kite/Yahoo/Polygon/NSE
interfaces only, no network access; see "Historical Data Platform"
below)
Phase 14 — Strategy Experiment Framework ✅ (`app/research/` -
create/register/run/compare/rank/score/export repeatable experiments
against the existing Backtest and Analytics Engines; does not optimize
strategies or change trading logic; see "Strategy Experiment
Framework" below and `docs/RESEARCH_GUIDE.md`)
Phase 15 — Parameter Injection Framework ✅ (`app/config/` -
StrategyParameters/RiskParameters/SessionParameters, immutable and
validated, replacing EMABreakoutStrategy's hardcoded constants and
RiskConfig's required-with-no-default fields; default configuration
reproduces identical pre-Phase-15 behavior; no optimization, no new
trading rules; see "Parameter Injection Framework" below and
`docs/PARAMETER_CATALOG.md`)
Phase 16 — Grid Search Strategy Optimization Engine ✅ (`app/optimization/` -
exhaustive, deterministic Cartesian-product search over
EMA Period/RSI thresholds/Reward-Risk Ratio/Risk %/Max Trades Per Day,
reusing the existing Experiment Framework unchanged; no AI, no strategy-
logic changes, no randomization; required a narrow, explicitly
CTO-authorized exception adding an optional strategy-parameter/
ema_period seam to `app.trading.backtest` - see "Parameter Injection
Framework" below and `docs/OPTIMIZATION_GUIDE.md`)
Phase 17 — Walk-Forward Validation Framework ✅ (`app/validation/` -
Rolling/Expanding/Anchored train-test windows; runs Grid Search on
training data only, tests the winner on unseen data only, and reports
a robustness score; entirely additive - every previously-frozen
package (including `app/optimization` and all of `app/trading`) is
untouched; see "Walk-Forward Validation Framework" below and
`docs/VALIDATION_GUIDE.md`)
Phase 18 — Monte Carlo Analysis Framework ✅ (`app/monte_carlo/` -
perturbs an already-completed backtest's trades (order, slippage,
commission, execution delay, missed trades, position sizing) many
times and measures the resulting distribution - Mean/Median Return,
Std Dev, 95% CI, VaR/CVaR, probability of profit/loss; does not
optimize, does not change trading logic; entirely additive - every
previously-frozen package untouched; see "Monte Carlo Analysis
Framework" below and `docs/MONTE_CARLO_GUIDE.md`)
Phase 19 — Paper Trading Architecture ✅ (`app/paper_trading/` -
event-driven design only: Order/Position/Portfolio models, a
synchronous EventBus, a BrokerInterface with PaperBroker (simulated
fills, no live connectivity), Order/Position/Portfolio managers, an
execution journal, a market session abstraction (no hardcoded NSE
calendar), and a performance monitor; does NOT execute trades, does
NOT connect to Zerodha, no continuous loop yet - that is the Paper
Trading Engine, a later phase; see "Paper Trading Architecture" below
and `docs/PAPER_TRADING_GUIDE.md`)
Phase 20 — Paper Trading Engine ✅ (`app/runtime/` - orchestrates the
existing, frozen platform (Indicators through Decision, Phases 5-10)
and the Phase 19 event-driven pieces into a single, replayable runtime
loop: `RuntimeEngine` drives a `MarketDataSource` (`StaticListSource`/
`HistoricalReplaySource`) one candle at a time via a synchronous
`Scheduler`, gated by a `SessionController` (Start/Pause/Resume/Stop/
Replay/End Session); `HealthMonitor` tracks processed candles,
latency, uptime, events published, orders generated, and current
state; creates NO new trading logic, connects to NO websocket/
Zerodha/REST API, has NO UI; see "Paper Trading Engine" below and
`docs/ENGINE_RUNTIME.md`)
Phase 21 — React Operations Dashboard ✅ (`frontend/src/` - an
operational control console for the Runtime Engine, not a marketing UI:
Header, Engine Controls (Start/Pause/Resume/Stop/Replay/Reset), and
Runtime/Market/Trading/Orders/Positions/Portfolio/Journal/Health panels
in a three-column trading-terminal layout; Zustand store backed by a
`DashboardService` interface, mocked this phase (`scripts/
dashboard_mock_data.json`, 60 synthetic candles) and designed to be
swapped for a real REST/WebSocket implementation without any
component/hook changing; contains NO trading logic, NO backend
connectivity, NO chart library (a static placeholder only); see "React
Operations Dashboard" below and `docs/DASHBOARD_GUIDE.md`)
Phase 22 — Backend Connectivity Layer ✅ (`backend/app/api/dashboard/` +
`frontend/src/services/api/` - replaces `MockDashboardService` with a
`RestDashboardService` polling `GET /api/dashboard`/`POST /api/runtime/
{start,pause,resume,stop,replay}` every second; zero changes to any
Dashboard component/layout/Zustand store/selector hook - only the data
provider changed, per the same `DashboardService` interface Phase 21
already defined; `DashboardRuntimeService` (backend) hosts a real,
frozen `app.runtime` session on a background thread against the
existing 75-candle sample dataset; found and fixed one real,
previously-latent defect (`Portfolio.drawdown`/`drawdown_percent`
plain `@property` methods are invisible to JSON serialization) entirely
within this phase's own new code, without touching the frozen
`app.paper_trading` package; still NO websocket, NO live broker; see
"React Operations Dashboard" below (updated) and `docs/API_GUIDE.md`)
Phase 23 — Zerodha Broker Adapter ✅ (`backend/app/brokers/` -
`ZerodhaBroker` implements the existing, frozen `BrokerInterface`
Protocol (`submit_order`/`cancel_order`, both typed against
`app.paper_trading.models.Order`) against the real Kite Connect API;
`PaperBroker` is untouched, and `OrderManager` never knows which
broker it holds. A thin `ZerodhaKiteClient` wraps the `kiteconnect` SDK
and translates every SDK exception into one of six typed exceptions
(`AuthenticationError`/`ConnectionError`/`OrderRejectedError`/
`RateLimitError`/`BrokerUnavailableError`/`MappingError`); explicit
mappers translate Kite orders/positions/holdings/profile into this
codebase's own types, never exposing a raw Kite object outside the
adapter. Credentials (`ZERODHA_API_KEY`/`ZERODHA_API_SECRET`/
`ZERODHA_ACCESS_TOKEN`/`ZERODHA_BASE_URL`) load from the environment,
deliberately independent of `app.kite`'s existing OAuth login-flow/
session database - a different concern (a human browsing market data)
from this adapter's (an automated system fed an already-generated
access token). Broker connectivity only: NO new trading logic, NO
changes to `app.runtime`, NO changes to `app.trading`; does NOT place
a real order this phase (a `trading_symbol_resolver` seam raises
`MappingError` loudly by default, since `Order` carries no instrument
identifier yet - deliberately Live Trading Mode's job, not this
adapter's); see "Zerodha Broker Adapter" below and
`docs/ZERODHA_ADAPTER_GUIDE.md`)

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
`TradingConditions.can_trade` are finally combined. CTO review after
Phase 10 froze the core domain architecture and inserted a
documentation/validation phase, then a Historical Backtesting phase,
before Paper Trading - proving the pipeline against historical data is
a separate concern from managing real (paper) positions against live
data. CTO review after Phase 11 froze Backtest Engine too and added a
Backtesting Analytics phase on top - analyzing a completed
`BacktestResult` (CAGR, regime/time-of-day breakdowns, ASCII charts,
...) is a separate concern from producing one. This is distinct from
item 15 below ("Analytics" for live paper trading) - that phase will
analyze real paper-trading history, not backtest results. CTO review
after Phase 12 froze the entire `app/trading/*` tree and `app/market_data`
too, adding a Historical Data Platform (`app/data/`) beneath all of
it - a single source of historical OHLCV data (import, validation,
storage, query, caching) is a separate concern from either replaying
that data (Backtesting) or analyzing the replay (Backtesting
Analytics); Backtesting itself still reads CSV directly for now and
will migrate to this platform as later, separately-reviewed work. CTO
review after Phase 13 froze `app/data` too, adding a Strategy
Experiment Framework (`app/research/`) that orchestrates the entire
frozen pipeline (Backtest Engine, then Analytics) into repeatable,
comparable experiments - explicitly not Strategy Optimization
(item 16 below), which is a separate, later phase. CTO review after
Phase 14 froze `app/research` too, adding a Parameter Injection
Framework (`app/config/`) that replaces hardcoded values in the two
modules not yet frozen (`app/trading/strategy`, `app/trading/risk`)
with validated, defaulted configuration objects - eliminating
hardcoded values is a separate concern from Strategy Optimization
(item 16 below), which needs this framework to exist first but does
not itself begin here. CTO review after Phase 15 froze `app/config`
too (alongside every other pre-Phase-15 package except `app/trading/
strategy`/`app/trading/risk`, which stay open), authorizing Strategy
Optimization itself: a Grid Search Engine (`app/optimization/`)
exhaustively evaluating combinations of EMA Period/RSI thresholds/
Reward-Risk Ratio/Risk %/Max Trades Per Day via the existing Experiment
Framework. Doing so surfaced a genuine architectural gap - the frozen
Backtest Engine had no way to inject a non-default `StrategyParameters`
or a non-default `ema_period` into an actual run, so half the six named
parameters could not yet change a real result - which the CTO
explicitly authorized fixing with a narrow, additive exception to
`app/trading/backtest`'s freeze (two new optional, default-preserving
fields) rather than accepting a degraded search space. This is
explicitly not Walk-Forward Validation (item 17 below) - testing
whether a winning configuration holds up on data the search never saw
is a separate concern from finding it. CTO review after Phase 16 froze
`app/optimization` too (alongside every other package, including all of
`app/trading` and `app/research` - no exception granted this time),
delivering Walk-Forward Validation (`app/validation/`) as a purely
additive orchestration layer: Rolling/Expanding/Anchored train-test
windows, running Grid Search on training data only and testing its
winner on unseen data only via the unmodified Experiment/Backtest/
Analytics Engines. This is explicitly not Monte Carlo Analysis (item 18
below), which is a separate, later phase. CTO review after Phase 17
froze `app/validation` too (every package created so far is now
frozen), delivering Monte Carlo Analysis (`app/monte_carlo/`) as
another purely additive package: it perturbs an already-completed
backtest's trade outcomes (order, slippage, commission, execution
delay, missed trades, position sizing) many times rather than
re-running the strategy, reusing `app.trading.backtest.performance.
calculate_max_drawdown` directly for the one piece of existing
arithmetic that applies unchanged. CTO review after Phase 18 froze
`app/monte_carlo` too (every package built so far is now frozen),
authorizing Paper Trading itself - split into an architecture phase
first: `app/paper_trading/` defines the complete event-driven design
(Order/Position/Portfolio models, an EventBus, a BrokerInterface with
a simulated-fill-only PaperBroker, managers, an execution journal, a
market session abstraction, a performance monitor) with no execution
and no Zerodha connectivity at all - deliberately separate from the
Paper Trading Engine (item 20 below), the continuous loop that will
actually drive these pieces against replayed or live data, which needs
this architecture reviewed and approved first rather than being built
sight-unseen alongside it. CTO review after Phase 19 froze
`app/paper_trading` too (every package built so far - `app/data`
through `app/paper_trading` - is now frozen), authorizing the Paper
Trading Engine itself: `app/runtime/` orchestrates the entire frozen
platform through the CTO's named ten-step flow (Receive Market Data →
Build IndicatorSnapshot → Build MarketContext → Evaluate
TradingConditions → Run Strategy Engine → Run Risk Engine → Publish
Events → Paper Broker → Portfolio Update → Journal → Performance
Monitor) without adding any new trading logic - every step is a call
into a package that already owns that decision. `MarketDataSource` and
`Scheduler` are both `Protocol` seams (mirroring `BrokerInterface`,
Phase 19's own seam) specifically so a live data feed or an
asynchronous scheduler can replace today's replay-only/synchronous
implementations later without `RuntimeEngine` changing at all. This is
explicitly not the React Dashboard (item 22 below), which remains a
separate, later, not-yet-authorized phase. CTO review after Phase 20
froze `app/runtime` too (every backend package built so far is now
frozen), authorizing the React Operations Dashboard itself -
`frontend/src/` (item 22 below, taken ahead of item 21's Analytics
phase at the CTO's direction): a Zustand-backed console with Engine
Controls, and Runtime/Market/Trading/Orders/Positions/Portfolio/
Journal/Health panels, entirely against a mock `DashboardService`
(`scripts/dashboard_mock_data.json`) - no REST call, no WebSocket, no
backend connectivity of any kind yet. Every panel reads through
exactly one hook, and every control button is a direct,
unconditional call into the service - no business logic in the
frontend, mirroring the same "orchestration, not computation"
discipline `app.runtime` itself was built to. This is explicitly not
backend connectivity (a separate, later, not-yet-authorized phase) -
see "React Operations Dashboard" below and `docs/DASHBOARD_GUIDE.md`
for the exact `DashboardService` seam a real backend will implement.
CTO review after Phase 21 froze the Dashboard's components/layout/
Zustand store/selector hooks too (alongside every backend package),
authorizing the Backend Connectivity Layer exactly along the seam
Phase 21 was designed for: `backend/app/api/dashboard/` exposes the
real `app.runtime` session over REST (`GET /api/dashboard`, `GET
/api/runtime/{health,state}`, `POST /api/runtime/{start,pause,resume,
stop,replay}`), and a new `RestDashboardService` (frontend) implements
the same `DashboardService` interface `MockDashboardService` already
did - polling on a 1-second interval, no WebSocket. Because the
interface was the seam, "no component changes" held exactly as
designed: every Dashboard component/layout/store/hook is untouched:
`services/index.ts`'s one assignment (`VITE_DASHBOARD_SERVICE=mock|
rest`) is the only thing that decides which implementation backs the
whole dashboard. This surfaced one genuine, previously-latent defect
in a frozen package - `app.paper_trading.models.Portfolio`'s
`drawdown`/`drawdown_percent` are plain `@property`, invisible to
Pydantic/FastAPI JSON serialization, since no REST endpoint existed
before this phase to expose `Portfolio` over JSON at all - fixed
entirely within this phase's own new code (a `PortfolioResponse`
subclass promoting both to `@computed_field`, reusing rather than
duplicating the frozen formula) without editing `app.paper_trading`
itself. This is explicitly not Zerodha integration (a separate, later,
not-yet-authorized phase) - see "React Operations Dashboard" below
(updated) and `docs/API_GUIDE.md`. CTO review after Phase 22 froze
`app/api/dashboard` and the Dashboard's backend-connectivity layer too
(every backend package is now frozen), authorizing the Zerodha Broker
Adapter itself: `app/brokers/` implements the existing, frozen
`BrokerInterface` Protocol (`app.paper_trading.broker_interface`,
Phase 19) against the real Kite Connect API, exactly the seam that
Protocol was designed for - `PaperBroker` is untouched, and
`OrderManager` never knows which broker it holds. Every Kite SDK call
goes through one seam (`KiteConnectClient`, mirroring
`app.market_data.client.MarketDataClient`'s established pattern), and
every SDK exception is translated into one of six typed exceptions
before it ever reaches a caller. Deliberately independent of
`app.kite`'s existing OAuth login-flow/session database - a different
concern (a human browsing market data through a logged-in browser
session) from this adapter's (an automated system fed an
already-generated access token via `ZERODHA_*` environment variables).
Broker connectivity only, per the CTO's explicit scope: no new trading
logic, no changes to `app.runtime`, no changes to `app.trading`. One
honestly-flagged limitation, not a defect - `app.paper_trading.models.
Order` carries no instrument identifier (`PaperBroker` never needed
one), so `ZerodhaBroker` cannot yet place a fully-real order end to
end; a `trading_symbol_resolver` seam raises `MappingError` loudly by
default rather than silently guessing, leaving real instrument
resolution to Live Trading Mode, the next, not-yet-authorized phase.
See "Zerodha Broker Adapter" below and `docs/ZERODHA_ADAPTER_GUIDE.md`.
Renumbered below.

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
11. Historical Backtesting — replay the existing pipeline over historical data ✅
12. Backtesting Analytics — CAGR/Sortino/regime/time analysis over a BacktestResult ✅
13. Historical Data Platform — import/validate/store/query historical OHLCV data ✅
14. Strategy Experiment Framework — repeatable, comparable experiments over the frozen pipeline ✅
15. Parameter Injection Framework — configurable, validated, defaulted strategy/risk parameters ✅
16. Grid Search Strategy Optimization Engine — exhaustive parameter search over the Experiment Framework ✅
17. Walk-Forward Validation — does a winning configuration hold up on unseen data ✅
18. Monte Carlo Analysis — perturbs trade outcomes, measures robustness under execution uncertainty ✅
19. Paper Trading Architecture — event-driven design: models, events, broker abstraction ✅
20. Paper Trading Engine — replayable runtime loop orchestrating the platform above ✅
21. Analytics — live paper-trading performance dashboard, statistics, reports
22. React dashboard — operational control console for the Runtime Engine ✅ (REST-connected to the real backend; mock mode still available via configuration)
23. Telegram notifications, deployment, production hardening

## Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite, Pandas, ta,
KiteConnect SDK, python-dotenv, Pydantic Settings, Uvicorn

**Frontend:** React, Vite, TypeScript, Zustand, Vitest, React Testing Library, oxlint, Prettier

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
│   │   ├── config/               # Parameter Injection Framework (Phase 15) - a
│   │   │   │                     # foundational/leaf package like core/; nothing in
│   │   │   │                     # app.trading may be imported here
│   │   │   ├── defaults.py       # Single source of DEFAULT_*/*_RANGE constants
│   │   │   ├── validation.py     # ParameterValidationError, validate_range/validate_less_than
│   │   │   ├── strategy_config.py  # StrategyParameters - injected into EMABreakoutStrategy
│   │   │   ├── risk_config.py    # RiskParameters - re-export of app.trading.risk.models.RiskConfig
│   │   │   ├── session_config.py   # SessionParameters - documented, NOT wired (conditions is frozen)
│   │   │   └── parameter_catalog.py  # PARAMETER_CATALOG - mirrored in docs/PARAMETER_CATALOG.md
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
│   │   │   │   └── ema_breakout.py  # EMABreakoutStrategy(parameters: StrategyParameters | None)
│   │   │   │                        # - Phase 15 injection; no-arg construction unchanged
│   │   │   ├── risk/            # Same purity constraints again - no approve/reject
│   │   │   │   ├── position_sizing.py, reward_risk.py, stop_loss.py, target.py,
│   │   │   │   │   daily_loss_limit.py, max_trades_per_day.py,
│   │   │   │   │   capital_exposure.py, max_concurrent_positions.py
│   │   │   │   ├── models.py    # RiskAssessment (frozen), RiskConfig (Phase 15: defaulted
│   │   │   │   │                # + range-validated via app.config), CapitalState
│   │   │   │   └── engine.py    # build_risk_assessment() - composes all evaluators
│   │   │   ├── decision/        # Same purity constraints again - no execution, no P&L
│   │   │   │   ├── models.py    # TradeRecommendation (frozen), StrategyCandidate
│   │   │   │   └── engine.py    # build_trade_recommendation() - selects among candidates
│   │   │   ├── backtest/        # Orchestrates the pipeline above - no duplicated logic
│   │   │   │   ├── loader.py        # CSV -> list[Candle]
│   │   │   │   ├── backtest_engine.py  # run_backtest() - candle-by-candle replay; Phase 16:
│   │   │   │   │                       # builds registry from config.strategy_parameters and
│   │   │   │   │                       # passes config.ema_period through (narrow, CTO-
│   │   │   │   │                       # authorized exception to this package's freeze)
│   │   │   │   ├── trade_executor.py   # simulates one open position's exit
│   │   │   │   ├── performance.py      # PerformanceReport, drawdown, streaks, Sharpe
│   │   │   │   ├── report.py           # console-formatted output
│   │   │   │   └── models.py    # BacktestConfig (Phase 16: + strategy_parameters/ema_period,
│   │   │   │                    # both default-preserving)/Trade/Result (frozen), PerformanceReport
│   │   │   └── analytics/       # Analyzes a BacktestResult - executes nothing
│   │   │       ├── analytics_engine.py   # build_analytics_report() - the single entry point
│   │   │       ├── performance_metrics.py  # CAGR, Sortino, Calmar, Recovery Factor
│   │   │       ├── equity_analysis.py      # total return, years elapsed, daily returns
│   │   │       ├── drawdown.py             # every drawdown episode, not just the deepest
│   │   │       ├── regime_analysis.py      # performance by Trend/Volatility/Momentum
│   │   │       ├── time_analysis.py        # performance by hour/weekday/session/expiry
│   │   │       ├── periodic_analysis.py    # yearly/monthly breakdowns
│   │   │       ├── trade_distribution.py   # holding time, Long/Short, exit reasons
│   │   │       ├── strategy_analysis.py    # per-strategy-name breakdown
│   │   │       ├── risk_analysis.py        # streaks, drawdown episodes, equity extremes
│   │   │       ├── report_builder.py       # console-formatted full report
│   │   │       ├── charts.py    # ASCII equity/drawdown/returns/distribution charts
│   │   │       └── models.py    # AnalyticsReport (frozen) and every section's model
│   │   ├── data/                 # Historical Data Platform - independent of app.trading
│   │   │   ├── models.py         # OHLCVRecord/Dataset/Instrument (frozen), ValidationReport
│   │   │   ├── repository.py     # HistoricalDataRepository - bisect-indexed range queries
│   │   │   ├── providers/
│   │   │   │   ├── provider_interface.py  # HistoricalDataProvider Protocol
│   │   │   │   ├── csv_provider.py        # CSVHistoricalDataProvider - implemented
│   │   │   │   └── stub_providers.py      # Kite/Yahoo/Polygon/NSE - interfaces only
│   │   │   ├── validation/
│   │   │   │   ├── validator.py  # missing/duplicate/out-of-order/OHLC/timezone checks
│   │   │   │   └── anomalies.py  # abnormal price move / abnormal volume detection
│   │   │   ├── cache/
│   │   │   │   └── cache_manager.py  # dataset + query caching, per-key invalidation
│   │   │   └── services/
│   │   │       ├── import_service.py  # provider -> repository, cache invalidation
│   │   │       └── query_service.py   # cached date-range queries, statistics, metadata
│   │   ├── research/             # Orchestrates the frozen pipeline - no optimization,
│   │   │   │                     # no trading-logic changes
│   │   │   ├── models.py         # Experiment/ExperimentResult (frozen), shared Metric enum
│   │   │   ├── experiment.py     # create_experiment() - id/created_date/git hash capture
│   │   │   ├── experiment_registry.py  # ExperimentRegistry - in-memory store, by id/tag
│   │   │   ├── experiment_runner.py    # run_experiment() - Backtest Engine + Analytics Engine
│   │   │   ├── comparison.py     # compare_experiments() - side-by-side metric table
│   │   │   ├── ranking.py        # rank_experiments() - sort by one configurable metric
│   │   │   ├── scoring.py        # calculate_scores() - configurable weighted scoring
│   │   │   └── export.py         # export_json()/export_csv()/export_markdown()
│   │   ├── optimization/         # Grid Search Strategy Optimization Engine (Phase 16) -
│   │   │   │                     # orchestrates app.research unchanged; no AI, no strategy-
│   │   │   │                     # logic changes, no randomization
│   │   │   ├── models.py         # OptimizationResult/Run/Report (frozen), GridValue
│   │   │   ├── parameter_space.py  # OptimizableParameter/ParameterSpace + DEFAULT_PARAMETER_CATALOG
│   │   │   │                       # (6 named parameters) + enforced "Do NOT optimize" guardrail
│   │   │   ├── grid_generator.py   # generate_grid() - deterministic Cartesian product
│   │   │   ├── executor.py       # run_grid_search() - builds StrategyParameters/RiskConfig
│   │   │   │                     # per combination, calls app.research unchanged
│   │   │   ├── progress.py       # ProgressTracker - completed/failed/elapsed/ETA
│   │   │   ├── ranking.py        # rank_optimization_results() - delegates entirely to
│   │   │   │                     # app.research.ranking/scoring, adds RankBy.WeightedScore
│   │   │   ├── report.py         # build_optimization_report()/render_markdown() - top/worst
│   │   │   │                     # 10, per-parameter summary, metric distributions
│   │   │   ├── export.py         # thin CSV/JSON/Markdown wrapper over app.research.export
│   │   │   └── optimizer.py      # optimize() - the one public entry point
│   │   ├── validation/           # Walk-Forward Validation Framework (Phase 17) - purely
│   │   │   │                     # additive; every previously-frozen package untouched
│   │   │   ├── models.py         # Window/WindowConfig/ValidationRules/Result/Run/Report (frozen)
│   │   │   ├── window_generator.py  # generate_windows() - Rolling/Expanding/Anchored
│   │   │   ├── validator.py      # evaluate_pass_fail() - configurable, no hardcoded thresholds
│   │   │   ├── runner.py         # run_walk_forward_validation() - optimize on train,
│   │   │   │                     # test the winner unchanged, via app.optimization/app.research
│   │   │   ├── report.py         # build_validation_report()/render_markdown() - robustness
│   │   │   │                     # score, train/test comparison, parameter stability
│   │   │   └── export.py         # CSV/JSON/Markdown of the window-by-window summary
│   │   ├── monte_carlo/          # Monte Carlo Analysis Framework (Phase 18) - purely
│   │   │   │                     # additive; perturbs trade outcomes, no strategy re-run
│   │   │   ├── models.py         # PerturbationConfig/SimulationResult/MonteCarloRun (frozen)
│   │   │   ├── perturbations/    # Each exposes apply(...); none knows about another
│   │   │   │   ├── trade_shuffle.py       # reorders trades; final total unaffected, path is
│   │   │   │   ├── slippage.py            # worsens entry/exit fill price by a percent
│   │   │   │   ├── commission.py          # subtracts a percent-of-notional/flat cost
│   │   │   │   ├── execution_delay.py     # delays fills N candles - needs the original candles
│   │   │   │   ├── missed_trade.py        # randomly drops trades by probability
│   │   │   │   └── position_variation.py  # randomly resizes quantity within a percent range
│   │   │   ├── simulation.py     # run_one_simulation() - chains enabled perturbations in one
│   │   │   │                     # fixed order, reuses calculate_max_drawdown for the rest
│   │   │   ├── runner.py         # run_monte_carlo_simulation() - N simulations, one seeded rng
│   │   │   ├── statistics.py     # compute_statistics() - mean/median/stddev/CI/VaR/CVaR
│   │   │   ├── report.py         # build_report()/render_markdown() - risk profile, worst/best
│   │   │   │                     # cases, rule-based recommendations
│   │   │   └── export.py         # CSV/JSON/Markdown of the report
│   │   ├── paper_trading/        # Paper Trading Architecture (Phase 19) - design only,
│   │   │   │                     # no execution, no Zerodha, no live connectivity
│   │   │   ├── models.py         # Order/Position/Portfolio (frozen) + ORDER_STATUS_TRANSITIONS
│   │   │   ├── events.py         # DomainEvent + every event on the bus (frozen)
│   │   │   ├── event_bus.py      # EventBus - synchronous publish/subscribe, dispatch by exact type
│   │   │   ├── broker_interface.py  # BrokerInterface Protocol - submit_order/cancel_order
│   │   │   ├── paper_broker.py   # PaperBroker - immediate simulated fill, no connectivity
│   │   │   ├── order_manager.py  # OrderManager - enforces ORDER_STATUS_TRANSITIONS, publishes events
│   │   │   ├── position_manager.py   # PositionManager - open/exit, realized+unrealized P&L
│   │   │   ├── portfolio_manager.py  # PortfolioManager - equity/drawdown from PositionManager
│   │   │   ├── execution_journal.py  # ExecutionJournal - subscribes to the bus, records everything
│   │   │   ├── market_session.py # MarketCalendar Protocol + ConfigurableCalendar - no hardcoded
│   │   │   │                     # NSE calendar, Pre-open/Open/Lunch/Close/After-hours/Holiday
│   │   │   └── performance_monitor.py  # PerformanceMonitor - fill ratio, latency, win rate,
│   │   │                               # daily return, max drawdown, all from observed events
│   │   ├── runtime/               # Paper Trading Engine (Phase 20) - orchestrates the
│   │   │   │                      # platform above; no new trading logic, no networking
│   │   │   ├── engine_config.py   # EngineConfig (frozen) - replay speed, candle limits,
│   │   │   │                      # auto-stop, session mode, logging level, random seed
│   │   │   ├── market_data_source.py  # MarketDataSource Protocol + StaticListSource/
│   │   │   │                      # HistoricalReplaySource - no websocket, no Zerodha
│   │   │   ├── session_controller.py  # SessionController - Start/Pause/Resume/Stop/
│   │   │   │                      # Replay/End Session, enforced via a transition table
│   │   │   ├── scheduler.py       # Scheduler Protocol + SynchronousScheduler - sync
│   │   │   │                      # today, replaceable by an async scheduler later
│   │   │   ├── health.py          # HealthMonitor/HealthSnapshot - processed candles,
│   │   │   │                      # latency, uptime, events published, orders generated
│   │   │   ├── event_processor.py # EventProcessor - the ten-step per-candle orchestration;
│   │   │   │                      # no indicator/strategy/risk/decision logic of its own
│   │   │   ├── runtime_engine.py  # RuntimeEngine - drives MarketDataSource through
│   │   │   │                      # EventProcessor via Scheduler, resumable across pauses
│   │   │   ├── startup.py         # RuntimeContext + start_runtime() - wires Event Bus ->
│   │   │   │                      # Managers -> Paper Broker -> Portfolio -> Runtime Engine
│   │   │   ├── shutdown.py        # ShutdownSummary + shutdown_runtime() - flush journal,
│   │   │   │                      # close session, print summary
│   │   │   └── replay.py          # run_replay() - start_runtime -> engine.run -> shutdown
│   │   │                          # in one call; deterministic for identical inputs
│   │   ├── brokers/               # Zerodha Broker Adapter (Phase 23) - broker
│   │   │   │                      # connectivity only, no new trading logic
│   │   │   ├── interface.py       # KiteConnectClient Protocol - the one seam to the SDK
│   │   │   ├── models.py          # BrokerPosition/BrokerHolding/BrokerProfile/BrokerOrder -
│   │   │   │                      # new types with no existing equivalent
│   │   │   ├── mapper.py          # Every Kite <-> internal translation, both directions;
│   │   │   │                      # reuses app.paper_trading.models.Order directly
│   │   │   ├── errors.py          # AuthenticationError/ConnectionError/OrderRejectedError/
│   │   │   │                      # RateLimitError/BrokerUnavailableError/MappingError
│   │   │   ├── authentication.py  # ZerodhaCredentials (env-loaded) - independent of
│   │   │   │                      # app.kite's OAuth login-flow/session database
│   │   │   ├── kite_client.py     # ZerodhaKiteClient - thin SDK wrapper, translates every
│   │   │   │                      # kiteconnect.exceptions.KiteException subclass
│   │   │   └── zerodha_broker.py  # ZerodhaBroker - implements BrokerInterface (frozen);
│   │   │                          # PaperBroker remains untouched
│   │   └── api/
│   │       ├── routes/
│   │       │   ├── health.py       # GET /health (includes DB connectivity check)
│   │       │   ├── kite_auth.py    # GET /auth/kite/login, /auth/kite/callback
│   │       │   └── market_data.py  # GET /market-data/{session,spot,candles,expiries,option-chain}
│   │       └── dashboard/          # Backend Connectivity Layer (Phase 22) - REST-exposes
│   │           │                   # the real app.runtime session; no websocket, no broker
│   │           ├── dashboard_service.py  # DashboardRuntimeService - hosts one live
│   │           │                   # RuntimeContext on a background thread; PortfolioResponse
│   │           │                   # (drawdown/drawdown_percent as @computed_field, fixing a
│   │           │                   # real Pydantic serialization gap without touching
│   │           │                   # app.paper_trading itself)
│   │           ├── dashboard_models.py   # DashboardSnapshotResponse/RuntimeStatsResponse -
│   │           │                   # reuse every frozen domain model directly
│   │           ├── dashboard_router.py   # GET /api/dashboard
│   │           ├── runtime_models.py     # ReplayRequest/RuntimeStateResponse
│   │           └── runtime_router.py     # GET /api/runtime/{health,state}, POST
│   │                               # /api/runtime/{start,pause,resume,stop,replay}
│   ├── tests/
│   │   ├── test_health.py
│   │   ├── test_repository.py
│   │   ├── kite/                # Auth tests use a fake Kite client - no
│   │   │                        # real network calls or credentials needed
│   │   ├── market_data/         # Same - a fake MarketDataClient, no real Kite calls
│   │   ├── config/               # Mirrors app/config/ - default/override/validation/
│   │   │                         # serialization tests, plus catalog<->markdown drift check
│   │   ├── trading/
│   │   │   ├── indicators/      # Pure math - no fakes/mocks needed at all
│   │   │   ├── context/         # Same - pure classification logic
│   │   │   ├── conditions/      # Same - pure permission logic
│   │   │   ├── strategy/        # Same - pure rule evaluation, one stub strategy for engine tests;
│   │   │   │                    # test_ema_breakout.py covers Phase 15's StrategyParameters injection
│   │   │   ├── risk/            # Same - pure numeric evaluation, no fakes/mocks needed;
│   │   │   │                    # test_models.py covers Phase 15's RiskConfig defaults/validation
│   │   │   ├── decision/        # Same - pure selection logic, no fakes/mocks needed
│   │   │   ├── backtest/        # Unit tests per module + one integration test
│   │   │   │                    # (test_backtest_engine.py) running the full replay;
│   │   │   │                    # Phase 16 added strategy_parameters/ema_period wiring tests
│   │   │   └── analytics/       # Unit tests per module + integration tests, including
│   │   │                        # a scale/performance-oriented test (see below)
│   │   ├── data/                # Mirrors app/data/ structure - unit tests per module
│   │   │                        # plus test_integration.py (CSV -> query -> statistics)
│   │   ├── research/            # Unit tests per module + test_experiment_runner.py -
│   │   │                        # a real integration test against the sample dataset
│   │   ├── optimization/        # Mirrors app/optimization/ - unit tests per module plus
│   │   │                        # real end-to-end grid search integration tests
│   │   ├── validation/          # Mirrors app/validation/ - window generation, pass/fail
│   │   │                        # rules, report/export, plus real end-to-end walk-forward
│   │   │                        # integration tests (Rolling/Expanding/Anchored)
│   │   ├── monte_carlo/         # Mirrors app/monte_carlo/ - one test file per perturbation,
│   │   │                        # simulation/statistics/runner (real backtest + determinism),
│   │   │                        # report, export
│   │   ├── paper_trading/       # Mirrors app/paper_trading/ - event bus, broker interface,
│   │   │                        # order/position lifecycle, portfolio accounting, journal,
│   │   │                        # performance monitor, market session
│   │   ├── runtime/             # Mirrors app/runtime/ - engine config, market data
│   │   │                        # sources, session controller, scheduler, health,
│   │   │                        # event processor, runtime engine, startup, shutdown,
│   │   │                        # replay determinism
│   │   ├── api/dashboard/       # Router/service/serialization tests (Phase 22) - a
│   │   │                        # fresh_service fixture swaps the module-level singleton
│   │   │                        # so tests never share one process-wide session
│   │   └── brokers/             # Mirrors app/brokers/ - a fake KiteConnectClient throughout,
│   │                            # no real API calls; authentication, order/position/holding/
│   │                            # profile mapping, exception translation, BrokerInterface compliance
│   ├── Dockerfile
│   ├── pyproject.toml           # ruff + mypy + pytest config
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── frontend/                     # React Operations Dashboard (Phase 21) - console for
│   │                             # the Runtime Engine; no trading logic, mock data only
│   ├── src/
│   │   ├── app/
│   │   │   ├── App.tsx          # Root shell - theme.css + DashboardPage
│   │   │   └── theme.css        # Dark trading-terminal design tokens (no animations)
│   │   ├── pages/
│   │   │   └── Dashboard/       # Three-column layout composition, no logic of its own
│   │   ├── components/
│   │   │   ├── Header/          # Title bar + session-state badge
│   │   │   ├── Controls/        # EngineControls - Start/Pause/Resume/Stop/Replay/Reset
│   │   │   ├── Runtime/         # Engine/session state, replay speed, counters, uptime
│   │   │   ├── Market/          # Current candle + market context; ChartPlaceholder (mock area)
│   │   │   ├── Trading/         # Latest signal, risk decision, trade recommendation
│   │   │   ├── Portfolio/       # Cash, equity, daily PnL, drawdown
│   │   │   ├── Orders/          # Open/filled/rejected orders, per-order status
│   │   │   ├── Positions/       # Open positions, quantity, entry, unrealized PnL
│   │   │   ├── Journal/         # Scrollable, newest-first event/signal/order/error log
│   │   │   ├── Health/          # Processing latency, fill ratio, events, engine health
│   │   │   └── Common/          # Panel/StatRow/Badge/DataTable/EmptyState + shared formatting
│   │   ├── hooks/               # useDashboardStore (Zustand) + one selector hook per panel
│   │   ├── services/            # DashboardService interface + Mock/RestDashboardService -
│   │   │   │                    # index.ts's one assignment picks which, via config.ts
│   │   │   │                    # (VITE_DASHBOARD_SERVICE=mock|rest); see docs/DASHBOARD_GUIDE.md
│   │   │   │                    # and docs/API_GUIDE.md
│   │   │   ├── api/             # Backend Connectivity Layer (Phase 22) - typed REST client
│   │   │   │   ├── client.ts    # apiRequest() - timeout (AbortController), typed errors
│   │   │   │   │                # (ApiHttpError/ApiTimeoutError/ApiNetworkError)
│   │   │   │   ├── dashboard.ts # getDashboardSnapshot() - GET /api/dashboard
│   │   │   │   ├── runtime.ts   # GET /api/runtime/{health,state}, POST .../{start,...}
│   │   │   │   └── wireTypes.ts # Exact snake_case backend response shapes
│   │   │   ├── restDashboardService.ts  # Polls GET /api/dashboard (1s default);
│   │   │   │                    # graceful retry on failure, no component-visible error state
│   │   │   ├── wireMapping.ts   # snake_case wire shapes -> camelCase types/*.ts, one place
│   │   │   ├── config.ts        # loadDashboardConfig() - every new env var, honest defaults
│   │   │   └── mockDataset.types.ts
│   │   ├── types/               # One file per backend domain area - runtime, market,
│   │   │   │                    # trading, orders, positions, portfolio, journal, health -
│   │   │   │                    # each mirroring a specific frozen backend model
│   │   │   └── dashboard.ts     # DashboardSnapshot - the one composed shape services emit
│   │   ├── setupTests.ts        # Vitest + Testing Library setup (jest-dom, cleanup)
│   │   ├── main.tsx
│   │   └── env.d.ts             # Typed Vite environment variables
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
├── scripts/
│   ├── dev-backend.sh
│   ├── dev-frontend.sh
│   ├── demo_pipeline.py         # Runs the live-trading pipeline end to end (Phase 10.5)
│   ├── demo_backtest.py         # Runs a historical backtest end to end (Phase 11)
│   ├── demo_analytics.py        # Runs a backtest + full analytics report (Phase 12)
│   ├── demo_data_platform.py    # Import/validate/store/query CSV data (Phase 13)
│   ├── demo_experiment_framework.py  # Create/run/compare/rank/export experiments (Phase 14)
│   ├── demo_parameter_framework.py   # Load/print/override/validate/inject config (Phase 15)
│   ├── demo_grid_search.py       # Small 3x2x2 grid search, top-5 ranking (Phase 16)
│   ├── demo_walk_forward.py      # Rolling-window validation + robustness score (Phase 17)
│   ├── demo_monte_carlo.py       # 100 simulations, shuffle+slippage+missed trades (Phase 18)
│   ├── demo_paper_architecture.py  # One full event sequence, no real trade (Phase 19)
│   ├── demo_runtime_engine.py    # Replays 100 candles through the Runtime Engine (Phase 20)
│   ├── dashboard_mock_data.json  # 60-candle mock replay dataset for the React Dashboard (Phase 21)
│   ├── demo_api_connectivity.md  # Backend/frontend startup, verifying REST connectivity,
│   │                             # Start/Pause/Resume against the real backend (Phase 22)
│   ├── demo_zerodha_adapter.py   # Auth, fetch profile, map order/position, handle an
│   │                             # error - all against a fake KiteConnectClient (Phase 23)
│   └── sample_data/
│       └── nifty_sample_candles.csv  # 75 synthetic candles, 3 trading days
├── docs/
│   ├── adr/                     # Architecture Decision Records - see docs/adr/README.md
│   ├── SYSTEM_ARCHITECTURE.md   # Complete technical architecture reference
│   ├── RESEARCH_GUIDE.md        # How to design, run, and judge experiments
│   ├── PARAMETER_CATALOG.md     # Every configurable parameter - name, type, default,
│   │                             # range, owning module, safe-to-optimize, reason
│   ├── OPTIMIZATION_GUIDE.md    # Grid search philosophy, avoiding overfitting, metric
│   │                             # interpretation, common mistakes
│   ├── VALIDATION_GUIDE.md      # Rolling/Expanding/Anchored, acceptance criteria,
│   │                             # interpreting robustness, recommended defaults
│   ├── MONTE_CARLO_GUIDE.md     # Simulation philosophy, VaR/CVaR, interpreting confidence
│   │                             # intervals, recommended defaults, limitations
│   ├── PAPER_TRADING_GUIDE.md   # Architecture, event flow, order/position lifecycle,
│   │                             # broker abstraction, migration path to live broker
│   ├── ENGINE_RUNTIME.md        # Runtime architecture, startup/shutdown sequence, replay
│   │                             # mode, lifecycle, failure handling, future live deployment
│   ├── DASHBOARD_GUIDE.md       # Dashboard layout, component hierarchy, state management,
│   │                             # backend integration plan, future WebSocket migration
│   ├── API_GUIDE.md             # REST endpoints, request/response models, polling
│   │                             # strategy, error handling, migration to WebSocket
│   └── ZERODHA_ADAPTER_GUIDE.md # Architecture, authentication flow, mapping philosophy,
│                                 # environment variables, error handling, migration to Live Trading
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

Originally (Phase 8) the RSI thresholds, VWAP/SuperTrend participation,
and minimum-agreeing-checks count above were module-level constants.
Phase 15 (Parameter Injection Framework) made all of them
constructor-injectable via `StrategyParameters`, defaulting to exactly
these same values - see "Parameter Injection Framework" below.

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
(capital deployed, trades already taken today, ...). Originally
(Phase 9) neither had defaults, forcing every caller to specify every
value explicitly. Phase 15 (Parameter Injection Framework) added
defaults to `RiskConfig`'s 7 fields, plus range validation it never had
- see "Parameter Injection Framework" below; `CapitalState` still has
no defaults, since live account state has no sensible static default.

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

## Historical Backtesting

`app/trading/backtest/` replays historical candles through the
existing pipeline unchanged - it calculates no indicator, evaluates no
strategy rule, and performs no risk calculation itself; every one of
those is a call into the package that already owns it
(`calculate_indicator_snapshot`, `build_market_context`,
`build_trading_conditions`, `run_strategies`, `build_risk_assessment`,
`build_trade_recommendation`). Confirmed by grep: no reimplemented
indicator/strategy/risk math anywhere in the package, and no
`fastapi`/`sqlalchemy`/`app.kite`/`kiteconnect` import.

`backtest_engine.py`'s `run_backtest(candles, config)` replays one
candle at a time, from `config.warmup_candles` onward (default 20,
safely above every indicator's minimum window). Each candle:

1. If a position is open, `trade_executor.check_exit()` checks
   stop-loss, then target, then end-of-day (stop-loss is checked first
   since a single candle's OHLC range can't reveal which level was
   actually touched first intrabar - a conservative, standard
   backtesting assumption).
2. If no position is open, the full pipeline runs on the candle history
   so far, producing a `TradeRecommendation`; a new position opens only
   when it recommends `Long` with a real position size (Phase 1 is
   long-only, per the brief).
3. Running capital, today's trade count, and today's realized loss feed
   a fresh `CapitalState` every candle - resetting the daily counters
   whenever the candle's calendar date changes - so `RiskAssessment`'s
   daily-loss/max-trades gates operate on real, live simulation state,
   not placeholders.
4. `TradingConditions`' previously "framework only" position-guard and
   cooldown parameters (Phase 7) now receive real data for the first
   time - `has_open_position` and `last_trade_closed_at` reflect this
   simulation's actual state - completing those gates with real input
   rather than redesigning them.

Two data gaps needed a minimal, flagged resolution (ADR-0007's
pattern, not a redesign): the CSV format this phase supports carries
no option-chain data, so `total_call_oi`/`total_put_oi` default to
`1`/`1` (PCR exactly `1.0`, neutral) and `price_change`/`oi_change`
default to `0.0` (Open Interest signal `NEUTRAL`) - callers with a
richer data source can override these. Separately, per-candle session
status is derived via the already-existing
`market_session_service.get_status(candle.timestamp)`, which reads the
*global* `app.core.config.settings.market_open`/`market_close`, not
`BacktestConfig`'s own - invisible while both default to "09:15"/"15:30",
but flagged in `backtest_engine.py`'s docstring since
`MarketSessionService` is an already-approved module this phase must
not redesign.

`performance.py` computes `PerformanceReport` from the resulting trade
history and equity curve alone - win rate, average/largest win and
loss, profit factor, expectancy, average reward/risk, max drawdown
(peak-to-trough over the equity curve), consecutive win/loss streaks,
and an annualized Sharpe ratio from daily returns (`None` when there
are fewer than 3 daily equity points or the return series has zero
variance - a missing Sharpe ratio is more honest than a misleading
one). `report.py` only formats already-computed figures for console
display - it recomputes nothing.

`scripts/demo_backtest.py` runs a complete backtest against
`scripts/sample_data/nifty_sample_candles.csv` (75 synthetic candles
across 3 trading days) and prints the results plus the first five
completed trades; no Zerodha credentials, network access, or FastAPI
server required:

```bash
python3 scripts/demo_backtest.py
```

## Backtesting Analytics

`app/trading/analytics/` analyzes a completed `BacktestResult` - it
executes no trade and changes no strategy behavior, only produces
analytics. `analytics_engine.py`'s `build_analytics_report()` is the
single entry point; every figure Phase 11 already computed (Sharpe
Ratio, Max Drawdown, win/loss counts, profit factor, expectancy,
average win/loss, reward/risk) is read straight from
`BacktestResult.report`, never recalculated - this package only adds
what Phase 11 didn't produce: CAGR, (linear) Annual Return, Sortino
Ratio, Calmar Ratio, Recovery Factor, yearly/monthly breakdowns, market
regime buckets, time-of-day buckets, full trade distribution, and
streak/drawdown detail beyond the single deepest drawdown. Confirmed by
grep: no reimplemented indicator/strategy/risk math, no trade
execution/order-placement terms, no `fastapi`/`sqlalchemy`/`app.kite`/
`kiteconnect` import, and nothing under `app/trading/indicators`,
`context`, `conditions`, `strategy`, `risk`, `decision`, or `backtest`
(all frozen this phase) was modified.

**Market Regime Analysis needed one flagged design decision.**
`BacktestResult` (frozen, Phase 11) never retained the `MarketContext`
each trade was entered under - Phase 11 didn't need one after deciding
whether to enter, so it was never stored, and Backtest Engine is frozen
this phase too, ruling out adding a field to capture one retroactively.
`regime_analysis.py` instead takes the original `candles` (the same
list `run_backtest()` was given) as an extra input alongside
`BacktestResult`, and recomputes `MarketContext` for exactly each
trade's entry candle by calling the same already-approved
`calculate_indicator_snapshot()`/`build_market_context()` functions
Backtest Engine itself calls - reuse, not a reimplementation of either,
and zero changes to any frozen file. A timestamp->index dict (built
once, O(n)) plus a per-index cache mean each unique candle's
`MarketContext` is computed at most once even across many trades.

**Two smaller gaps got the same minimal, flagged treatment**
(ADR-0007's pattern): `AnalyticsConfig.expiry_dates` defaults to empty
- this CSV framework has no options-expiry concept (the same class of
gap as Phase 11's neutral PCR/OI defaults) - so the "Expiry Day vs
Non-Expiry Day" bucket is empty rather than fabricated whenever it
isn't supplied. And Calmar Ratio's denominator (`max_drawdown_percent`)
is computed relative to *initial* capital, a simplified convention,
since Phase 11's `PerformanceReport.max_drawdown` is an absolute
currency figure, not the peak-relative percentage a stricter Calmar
definition would use.

**Efficiency for several years of history.** Every aggregation (yearly/
monthly grouping, drawdown-episode detection, streak counting, equity
extremes) is a single O(n) pass - never nested loops over the full
trade list or equity curve. Regime analysis's per-index caching (above)
keeps it from ever recomputing the same candle's `MarketContext` twice.
This wasn't verified against real 5-10 years of NIFTY data (this
sandbox has no network access to source it, and generating and
replaying tens of thousands of synthetic candles through the full
pipeline isn't practical within a unit test's time budget) - instead,
`test_analytics_scales_to_a_larger_dataset_without_quadratic_blowup`
(marked `slow`) runs the same pipeline at two dataset sizes (a 4x
candle-count increase) and asserts the runtime doesn't grow anywhere
near quadratically, as a smaller-scale proxy that would still catch an
accidental O(n²) regression.

`report_builder.py` formats the full report (Overall Performance,
Yearly/Monthly tables, Market Regime, Time Analysis, Trade
Distribution, Risk Analysis, Strategy Breakdown) and `charts.py` renders
console-only ASCII charts (Equity Curve, Drawdown Curve, Monthly
Returns, Trade Distribution) - both downsampled to a fixed column width
first, so a chart stays readable regardless of how many candles
produced the underlying data. No external plotting library is used
anywhere.

`scripts/demo_analytics.py` runs a complete backtest against the same
sample CSV as `demo_backtest.py`, then the full analytics report over
its result - no Zerodha credentials, network access, or FastAPI server
required:

```bash
python3 scripts/demo_analytics.py
```

## Historical Data Platform

`app/data/` is intended to become the single source of historical
market data for the entire application - Backtesting currently reads
CSV directly (Phase 11, frozen) and will migrate to this platform as
later, separately-reviewed work, not silently as part of this phase.
`app/market_data` and every `app/trading/*` package (through
Analytics, Phase 12) are frozen this phase too - none of them were
touched; `app/data` sits beneath all of it, with its own repository,
cache, providers, and validation, importable by anything without
requiring any of them to change first.

**Data model.** `OHLCVRecord` is a new model, not a reuse of
`app.market_data.schemas.Candle` (frozen, and without room for what
this platform needs): `app.market_data` is the live, Kite-facing
layer, while `app.data` is this platform's own historical storage
representation, with `open_interest` and a generic `metadata` slot -
future-ready for PCR and option Greeks without inventing precise field
names for data this phase doesn't carry. `Instrument`
(symbol/exchange/timeframe/name/lot_size/tick_size) and `DatasetKey`
(the symbol/exchange/timeframe identity used to key everything) are
separate types - metadata *about* an instrument versus the identity
used to look up its data. Every model is frozen (ADR-0006); `Dataset.candles`
is a `tuple`, not a `list` - `frozen=True` only stops *reassigning* an
attribute, it does not stop mutating a mutable object already
referenced by one, so a dataset's actual stored data needed to be
genuinely immutable, not merely frozen-looking.

**Providers.** `HistoricalDataProvider` is a `Protocol` with one method
- `fetch(start, end)` - so a CSV file and a future network provider
are interchangeable. `CSVHistoricalDataProvider` is fully implemented.
`KiteHistoricalProvider`/`YahooHistoricalProvider`/
`PolygonHistoricalProvider`/`NSEHistoricalProvider` exist as
interfaces only - each structurally conforms to the Protocol but
raises `NotImplementedError`, per this phase's explicit "no network
access yet". `CSVHistoricalDataProvider` is deliberately independent of
`app.trading.backtest.loader` (Phase 11's own CSV loader) rather than
reusing it: the dependency direction for this platform must run the
other way (Backtesting will eventually depend on `app.data`, not the
reverse), so `app.data` cannot import from `app.trading.backtest`
without inverting that - confirmed by grep, no such import exists.

**Validation.** `validation/validator.py` checks missing timestamps
(gaps within the same calendar date only - a gap across days is
expected, markets close overnight, and there's no exchange holiday
calendar available, the same limitation already flagged for
`app.market_data.market_session` since Phase 4; skipped entirely for
daily-timeframe datasets), duplicate timestamps, out-of-order candles,
negative prices/volume, OHLC consistency (`High >= Open/Close` and
`Low <= Open/Close` as distinct, separately-typed issues), and
timezone consistency. `validation/anomalies.py` separately detects
abnormal single-candle price moves and abnormal volume (z-score
against the dataset's own mean/std-dev). Comparing timestamps for
ordering/gap detection normalizes aware datetimes to naive UTC first
(`_comparable()`) - comparing a naive and an aware `datetime` directly
raises `TypeError` in Python, which would otherwise crash validation
on exactly the kind of mixed-timezone dataset the timezone-consistency
check exists to catch; found and fixed via a real test failure, not
assumed. `validate_dataset()` never raises - it always returns a
`ValidationReport`; the repository is what decides what to do with it.

**Repository.** `HistoricalDataRepository.import_dataset()`/
`replace_dataset()`/`append_dataset()` all validate before storing and
raise `DatasetValidationError` (carrying the full `ValidationReport`)
when the result isn't valid, unless the caller passes `force=True` -
data quality problems are surfaced by default, not silently persisted.
Each dataset's candles are stored once, sorted by timestamp, alongside
a parallel tuple of just the timestamps built at import/replace/append
time (not on every query) - `query_date_range()` binary-searches
(`bisect`) that tuple for its start/end bounds in O(log n) and copies
out only the matching slice, the concrete answer to "avoid loading
unnecessary data into memory" across several years of intraday
candles. `query_single_day()`, `query_latest_candle()`,
`query_instrument()`, `get_instrument_metadata()`, `list_instruments()`,
and `dataset_statistics()` round out the repository's methods.

**Cache.** `CacheManager` caches whole datasets and individual
date-range query results, both invalidated per-key
(`invalidate_dataset()`) rather than only by a global clear - importing
new data for one instrument must not force every other cached
instrument to be recomputed. `ImportService` invalidates the relevant
cache entry on every import; `QueryService` transparently checks the
cache before delegating a date-range query to the repository.

`scripts/demo_data_platform.py` imports the same sample CSV via
`CSVHistoricalDataProvider`, validates it, stores it, queries a date
range, and prints statistics and the validation report - no Zerodha
credentials, network access, or FastAPI server required:

```bash
python3 scripts/demo_data_platform.py
```

## Strategy Experiment Framework

`app/research/` manages experiments - it does not optimize strategies
and does not change trading logic; it orchestrates repeatable research
by invoking the existing (frozen) Backtest Engine and Analytics Engine.
Full usage guidance, workflow, and metric interpretation live in
`docs/RESEARCH_GUIDE.md`; this section covers the architecture.

**Two frozen types, not one mutable record.** `Experiment`
(`models.py`) is the immutable *definition* of a run - name,
description, strategy, dataset path, timeframe, `parameters` (see
below), seed, tags, notes, and a best-effort git commit hash - created
once via `experiment.create_experiment()`. `ExperimentResult` is
produced by actually running one
(`experiment_runner.run_experiment()`): the `Experiment` plus its
`BacktestResult`, `AnalyticsReport`, status, and duration. This mirrors
why every other domain model in this codebase is frozen (ADR-0006) -
`Experiment` itself never changes after creation; running it produces
a new, separate, immutable result, rather than mutating fields onto it
in place.

**`parameters` is deliberately inert.** `Experiment.parameters` is a
free-form `dict[str, str | int | float | bool]` - stored and exported,
never interpreted, exactly per this phase's brief ("must NOT understand
these values"). The two things that actually drive a real backtest run
are `Experiment.backtest_config` and its nested `risk_config` - the
real, existing, tunable surface the frozen Backtest Engine already
accepts (`risk_per_trade_percent`, `stop_loss_atr_multiplier`,
`max_daily_loss`, session/window settings, ...). The frozen
`EMABreakoutStrategy` has no external parameterization hook at all
today (its RSI thresholds are module-level constants), so an example
like `"ema_period": 20` in `parameters` records intent, not something
the strategy currently reads - wiring arbitrary strategy parameters
through is Strategy Optimization's job (the next phase, not this one).
See `docs/RESEARCH_GUIDE.md`'s "Parameter management" section.

**The runner orchestrates, it doesn't calculate.**
`experiment_runner.run_experiment()` loads candles via the same
`app.trading.backtest.loader.load_candles_from_csv()` Backtest Engine's
own demo scripts use (deliberately not `app.data`, since Phase 13's own
summary explicitly deferred that migration as separate, later work),
calls `run_backtest()`, then `build_analytics_report()`, and packages
the result - timing the whole call and catching any failure (bad
dataset path, too few candles, ...) as a `FAILED` `ExperimentResult`
with the error recorded, rather than raising and aborting a batch of
many experiments. `ExperimentRegistry` is an in-memory store (mirroring
`StrategyRegistry`'s and `HistoricalDataRepository`'s patterns) keyed
by experiment id, with lookup by tag.

**Comparison, ranking, and scoring share one metric mapping.**
`models.Metric` (`NetProfit`, `ProfitFactor`, `Expectancy`,
`MaxDrawdown`, `RecoveryFactor`, `SharpeRatio`, `CalmarRatio`,
`WinRate`) and `models.extract_metric()` are the one place any of
`comparison.py`, `ranking.py`, or `scoring.py` read
`AnalyticsReport.overall` - not three separate mappings that could
drift. `ranking.rank_experiments()` sorts by one metric, always putting
missing values (a `FAILED` result, or a metric Analytics itself
couldn't compute) last regardless of the metric's direction.
`scoring.calculate_scores()` min-max normalizes each metric *across the
batch being scored together* (there's no universal scale a raw Net
Profit and a raw Sharpe Ratio could otherwise share), inverting
`MaxDrawdown` first since it's the one metric where lower is better,
then applies the caller's weights exactly as given - it does not
require them to sum to 1.0/100%, since enforcing that would be an
opinion this framework doesn't need to hold.

**Export.** `export_json()`/`export_csv()`/`export_markdown()` all read
from one shared `_build_summary()` so the fields present never drift
between formats - experiment metadata, its parameter set (each
prefixed `param_` in the flattened JSON/CSV output), key performance
metrics, and rank position when a ranking is supplied.

`scripts/demo_experiment_framework.py` creates three experiments
against the same sample CSV (varying only `risk_per_trade_percent`/
`stop_loss_atr_multiplier` - the real, wired-in configuration, per
"parameters is deliberately inert" above), runs them, compares and
ranks them, computes a weighted score, and exports all three formats -
no Zerodha credentials, network access, or FastAPI server required:

```bash
python3 scripts/demo_experiment_framework.py
```

## Parameter Injection Framework

`app/config/` eliminates the hardcoded strategy/risk values that
Phase 14's `RESEARCH_GUIDE.md` flagged as a gap ("the frozen
`EMABreakoutStrategy` has no external parameterization hook at all").
It introduces no optimization and no new trading rules - every default
below reproduces the exact pre-Phase-15 behavior, and the full 375-test
suite that existed before this phase passes completely unchanged.
Full per-parameter documentation lives in `docs/PARAMETER_CATALOG.md`;
this section covers the design.

**Only two modules were actually modified.** Every prior phase
(`app/data`, `app/market_data`, `app/trading/context`,
`app/trading/conditions`, `app/trading/decision`, `app/trading/backtest`,
`app/trading/analytics`, `app/trading/indicators`, `app/research`)
stayed frozen - `git diff --stat` against every one of them is empty.
`app/trading/strategy/ema_breakout.py` and `app/trading/risk/models.py`
were the two modules the CTO brief explicitly authorized touching.

**`StrategyParameters` is genuinely wired.**
`EMABreakoutStrategy.__init__(self, parameters: StrategyParameters |
None = None)` stores `parameters or StrategyParameters()`, so
`EMABreakoutStrategy()` (the existing, unchanged call in
`registry.default_registry()`) uses exactly the same RSI thresholds
(55.0/45.0) and minimum-agreeing-checks (4) that were previously
module-level constants. VWAP and SuperTrend, previously unconditional,
gained real `vwap_enabled`/`supertrend_enabled` toggles (default `True`
each, so nothing changes by default) - disabling one now genuinely
removes it from the vote, and `_strength_for()` was made relative to
however many checks actually ran (5 by default, fewer with a check
disabled) rather than hardcoding "5".

**`RiskConfig` gained defaults and validation, not a new model.**
`app.trading.risk.models.RiskConfig` already was the immutable Pydantic
config object the brief describes (Phase 9) - it just required all 7
fields with no defaults and validated nothing. Both were verified safe
to add: every existing construction site (five of them, across
`tests/trading/risk|backtest/analytics/helpers.py` and
`tests/research/helpers.py`) already passed every field explicitly, so
adding defaults sourced from `app.config.defaults` changes nothing for
any existing caller. `app.config.risk_config` does not duplicate
`RiskConfig`'s 7 fields into a second model - it re-exports the same
class as `RiskParameters` (via a deferred `__getattr__` in
`app/config/__init__.py`, to avoid a real circular import between
`app.trading.risk.models` -> `app.config` -> `app.config.risk_config`
-> back to `app.trading.risk.models`), purely so `from app.config import
RiskParameters` can't be confused with `from app.trading.risk.models
import RiskConfig` at an import site.

**Several brief-named examples are honest, unconnected placeholders,
not fake wiring.** `SessionParameters` (Opening Range Minutes, Trading
Start/End Time, Lunch Filter, Expiry Filter) maps entirely onto
`app.trading.conditions`, which is frozen this phase - it exists so
these parameters are documented and validated with the right shape,
without inventing a connection. "Lunch Filter" specifically has no
existing counterpart anywhere in this codebase. Likewise, EMA/RSI/ATR
periods and SuperTrend's period/multiplier are not fields on
`StrategyParameters` at all: `EMABreakoutStrategy` never computes
indicators itself, so those periods belong to
`app.trading.indicators.engine.calculate_indicator_snapshot`, already a
keyword parameter there (matching defaults) since Phase 5 - but its only
callers (`app.trading.backtest`, `app.trading.analytics`) are frozen, so
wiring them through `app.config` needs a later, separately-reviewed
phase. `docs/PARAMETER_CATALOG.md` documents every one of these
placeholders explicitly rather than silently omitting them, following
the same "unconnected placeholder" pattern as Phase 14's
`Experiment.parameters`.

**Validation lives on the models, not in a separate rules engine.**
`app/config/validation.py` holds one shared `ParameterValidationError`
and two reusable helpers (`validate_range`, `validate_less_than`); each
config model (`StrategyParameters`, `RiskConfig`, `SessionParameters`)
calls them from its own `@model_validator(mode="after")` - range checks
per field, plus one real invalid-combination check each
(`rsi_bearish_threshold < rsi_bullish_threshold`;
`min_agreeing_checks <= 3 + vwap_enabled + supertrend_enabled`;
`trading_start_time < trading_end_time`).

`scripts/demo_parameter_framework.py` loads every default configuration,
prints the full parameter catalog, overrides selected `StrategyParameters`
values (and shows an invalid combination being rejected), then runs the
same `IndicatorSnapshot`/`MarketContext`/`TradingConditions` through both
a default-configured and an overridden `EMABreakoutStrategy` side by
side - proving the strategy actually reads the injected values, not just
holds onto them:

```bash
python3 scripts/demo_parameter_framework.py
```

## Grid Search Strategy Optimization Engine

`app/optimization/` exhaustively evaluates a Cartesian product of
strategy/risk parameter combinations against the existing (frozen)
Strategy Experiment Framework - no AI, no strategy-logic changes, no
randomization. Full usage guidance, grid search philosophy, and
overfitting pitfalls live in `docs/OPTIMIZATION_GUIDE.md`; this section
covers the architecture.

**A CTO-authorized narrow exception to `app.trading.backtest`'s
freeze, decided before any code was written.** Planning this phase
surfaced that `run_backtest()` always built `default_registry()` with
no override and never passed `ema_period` to the indicator engine -
meaning half the six parameters the CTO brief names (EMA Period, RSI
Bullish/Bearish Threshold) could not change a real result no matter
what `app.optimization` did, only Reward/Risk Ratio, Risk %, and Max
Trades Per Day (already reachable via `RiskConfig`) could. Rather than
silently ship a degraded search space or silently touch a frozen
package, this was surfaced as an explicit choice; the CTO chose to
authorize a minimal, additive fix: `BacktestConfig` gained
`strategy_parameters: StrategyParameters | None = None` and
`ema_period: int = 20`, and `backtest_engine.py` now builds its
registry from `config.strategy_parameters` (instead of the
parameterless `default_registry()`) and threads `config.ema_period`
through to `calculate_indicator_snapshot()`. Both defaults exactly
reproduce prior behavior - every pre-Phase-16 `BacktestConfig(...)`
call site and every previously-passing test is unaffected (474 tests
pass unchanged plus this phase's own 60+13 new ones).

**Parameter space, not parameter catalog.** `parameter_space.py`'s
`OptimizableParameter` (Name/Description/Type/Minimum/Maximum/Step/
Default/Safe To Optimize) is deliberately a different shape from
Phase 15's `ParameterDescriptor` - this one needs a swept numeric
range, not a documented default. `DEFAULT_PARAMETER_CATALOG` covers
exactly the CTO brief's six named parameters; the "Do NOT optimize"
list (VWAP/SuperTrend toggles, every session filter, the expiry
filter) is an *enforced* guardrail - `ParameterSpace`/
`OptimizableParameter` raise `ParameterValidationError` if asked to
include one, not just a comment saying not to.

**Six parameters, three real mappings.** `executor.py` applies each
grid combination as: `risk_percent` -> `RiskConfig.
risk_per_trade_percent`; `max_trades_per_day` -> `RiskConfig.
max_trades_per_day`; `reward_risk_ratio` -> `RiskConfig.
target_atr_multiplier = reward_risk_ratio * stop_loss_atr_multiplier`
(holding the base config's stop-loss multiplier fixed - a real,
pre-existing relationship, since both distances are `atr * their own
multiplier` and `atr` cancels out of the ratio); `rsi_bullish_
threshold`/`rsi_bearish_threshold` -> `StrategyParameters`; `ema_period`
-> `BacktestConfig.ema_period` directly. Every combination becomes its
own `Experiment` via the unmodified `app.research.experiment.
create_experiment()`, with the grid values recorded in
`Experiment.parameters` too (so they appear automatically as
`param_*` columns/fields in every export) - reusing Phase 14's
framework completely rather than reimplementing backtest
orchestration.

**Ranking and export duplicate nothing.** `ranking.py`'s `RankBy`
covers the CTO brief's seven modes; six (`ProfitFactor`, `NetProfit`,
`SharpeRatio`, `RecoveryFactor`, `MaxDrawdown`, `WinRate`) delegate
directly to `app.research.ranking.rank_experiments()`/`extract_metric()`,
and the default `WeightedScore` delegates to `app.research.scoring.
calculate_scores()` with a documented default weighting (Profit Factor
and Sharpe Ratio at 0.3 each, Recovery Factor and Win Rate at 0.2 each -
see `docs/OPTIMIZATION_GUIDE.md` for the reasoning, and callers may
supply their own `ScoringWeights`). `export.py` is a thin wrapper that
unwraps `OptimizationResult.experiment_result` and calls straight into
`app.research.export`'s three functions - no CSV/JSON/Markdown writing
is reimplemented. `report.py` is the one genuinely new artifact
(top/worst 10, per-parameter summary, metric distributions, run
statistics) - a different, aggregate view from `export.py`'s flat
per-combination table, matching the CTO brief's separate REPORT/EXPORT
sections.

`scripts/demo_grid_search.py` runs the CTO brief's own example search
space (3 EMA periods x 2 RSI bullish thresholds x 2 reward/risk ratios,
12 combinations) against the sample dataset, printing every
combination's weighted score, the best configuration, and a top-5
ranking - no Zerodha credentials, network access, or FastAPI server
required:

```bash
python3 scripts/demo_grid_search.py
```

## Walk-Forward Validation Framework

`app/validation/` evaluates whether an optimized configuration
generalizes to unseen market data - it is **not another optimizer**,
it orchestrates the existing Grid Search Optimization Engine (training
only) and the existing Experiment/Backtest/Analytics Engines (testing
only), then compares the two. Full usage guidance, window-type
tradeoffs, and how to interpret a robustness score live in
`docs/VALIDATION_GUIDE.md`; this section covers the architecture.

**Entirely additive - no exception needed this time.** Every package
this phase's CTO brief listed as frozen (`app/data`, `app/config`,
`app/market_data`, all of `app/trading`, `app/research`,
`app/optimization`) has a completely empty `git diff` - unlike Phase
16, nothing required a narrow exception here, since this package only
ever calls into existing, already-parameterized entry points
(`app.optimization.optimizer.optimize()`, `app.research.experiment.
create_experiment()`/`experiment_runner.run_experiment()`).

**Three window types, three real generator behaviors.**
`window_generator.py`'s Rolling/Expanding/Anchored aren't just labels -
each produces a genuinely different sequence: Rolling slides both
train and test windows forward by a fixed step, keeping train duration
constant; Expanding fixes the train start and grows train duration
each iteration; Anchored fixes the *entire* train window after the
first iteration and only slides the test window. All three are
deterministic (no randomization) and stop the instant a window's test
period would exceed the available data - no partial final window is
ever produced.

**Train/test data reaches existing, frozen, file-path-based APIs via
temporary CSVs, not a new loading mechanism.** `app.optimization`/
`app.research`'s existing entry points take a `dataset_path: str` (per
`app.trading.backtest.loader.load_candles_from_csv`) - `runner.py`
loads the full dataset once, slices each window's train/test candles
by timestamp, and writes them to temporary per-window CSV files
(cleaned up when the run finishes) purely so the existing frozen
contract can be called unmodified. This is I/O plumbing to interface
with an existing interface, not a reimplementation of anything
`app.optimization`/`app.research` already do.

**Two distinct data-sufficiency gates, not one.**
`WindowConfig.minimum_candles` rejects a window before any optimization
runs, if either its train or test slice is too short. Separately,
`WindowConfig.minimum_trades` rejects a window *after* training
optimization picks a "best" configuration, if that configuration made
fewer trades than the minimum during training - a "best" pick built on
too few trades isn't trustworthy enough to test at all. Both produce
`WindowStatus.INSUFFICIENT_DATA`, distinct from `FAILED` (an actual
exception) and `COMPLETED`.

**Pass/fail rules are entirely configurable - `ValidationRules` has no
default values**, the same "nothing hardcoded" discipline Phase 9's
original `RiskConfig` established: constructing `ValidationRules()`
with zero arguments raises immediately. Four per-window rules
(`max_drawdown_increase_percent`, `min_profit_factor`,
`max_performance_degradation_percent`, `min_trade_count`) plus one
run-level rule (`min_robustness_score_percent`) - see
`docs/VALIDATION_GUIDE.md` for each rule's exact meaning, its
zero-base-case handling, and recommended (not hardcoded) starting
values.

**The robustness score is deliberately simple, not a hidden formula.**
`ValidationReport.robustness_score` is the percentage of *completed*
windows that passed every configured rule - not a continuous,
degradation-weighted score. This is an explicit transparency trade-off
(see `docs/VALIDATION_GUIDE.md`'s "Interpreting robustness"): a score a
reader can audit by hand, over one that would need reverse-engineering
to trust.

`scripts/demo_walk_forward.py` generates a small synthetic weekday
dataset, runs Rolling-window validation with a single-parameter search
space, prints every window's train/test comparison, and reports the
overall robustness score - no Zerodha credentials, network access, or
FastAPI server required:

```bash
python3 scripts/demo_walk_forward.py
```

## Monte Carlo Analysis Framework

`app/monte_carlo/` evaluates strategy robustness under realistic
execution uncertainty by perturbing an already-completed backtest's
trades - it does **not** optimize and does **not** change trading
logic. Full simulation philosophy, VaR/CVaR conventions, and
limitations live in `docs/MONTE_CARLO_GUIDE.md`; this section covers
the architecture.

**Perturbs outcomes, never re-runs the strategy.** Unlike every prior
robustness-checking phase (Grid Search re-runs backtests with different
configuration; Walk-Forward re-runs the whole optimize-then-test cycle
per window), Monte Carlo takes one already-completed
`BacktestResult.trades` and perturbs the *trades themselves* - a
different fill price, a dropped trade, a different sequence - then
recomputes what the resulting equity curve and drawdown would have
been. No indicator, strategy, or risk calculation happens anywhere in
this package.

**Six independent perturbations, one fixed chain.** Each
`app/monte_carlo/perturbations/` module exposes a pure `apply(...)`
function and imports nothing from any other perturbation module -
`simulation.py` is the only place that chains whichever `
PerturbationConfig` enables, in one fixed, documented order (trade
shuffle → slippage → commission → execution delay → missed trades →
position variation), so the same seed always reproduces the exact same
result. Trade Order Shuffle is the odd one out: it reorders the trade
*list* rather than adjusting any trade's own numbers, which is enough
on its own, since `simulation.py` builds its equity curve by cumulative
pnl in *list order*, not by each trade's own timestamp.

**Execution Delay needs the original candles - the same precedent
`app.trading.analytics.regime_analysis` already established.** Every
other perturbation only needs the trade list; delaying a fill by N
candles requires looking up the real close price N candles later,
which means the original candle series has to be supplied as a
separate input alongside the `BacktestResult` - not a new pattern,
just the same one Phase 12 used for exactly the same reason.

**Reuses `calculate_max_drawdown` directly, but not
`build_performance_report`/`calculate_sharpe_ratio`.** The former only
ever reads `EquityPoint.equity` in list order, so it applies unchanged
to a perturbed (possibly shuffled) trade sequence. The latter both
group by calendar date internally - meaningless once trade order has
been shuffled away from real chronological order - so this package
computes its own minimal return/drawdown per simulation instead of
reusing them, avoiding a misleading Sharpe number rather than silently
producing one.

**VaR and CVaR are computed non-parametrically**, directly from the
simulated return distribution's own percentiles - no assumption that
returns are normally distributed. `statistics.py` is the one genuinely
new piece of arithmetic this phase adds (no existing package computes
VaR/CVaR/confidence intervals across many simulated outcomes); see
`docs/MONTE_CARLO_GUIDE.md` for the exact convention and worked
interpretation.

**Recommendations are threshold-triggered template strings, not AI.**
`report.py` checks the computed statistics against a few fixed,
documented thresholds (high loss probability, drawdown inflation
relative to the original backtest, a wide confidence interval) and
always includes a disclaimer that these are statistical observations
from perturbed historical trades, not a guarantee about future
performance.

`scripts/demo_monte_carlo.py` runs a real backtest against a small
synthetic dataset, then 100 Monte Carlo simulations with Trade Order
Shuffle, 0.10% slippage, and 1% missed trades enabled - printing mean
return, the 95% confidence interval, worst drawdown, probability of
profit, and top risk metrics:

```bash
python3 scripts/demo_monte_carlo.py
```

## Paper Trading Architecture

`app/paper_trading/` defines the complete event-driven architecture
for paper trading - it does **not** execute trades and does **not**
connect to Zerodha or any live market data. Full architecture diagrams,
event flow, and the migration path to a live broker live in
`docs/PAPER_TRADING_GUIDE.md`; this section covers the key design
decisions.

**A frozen value plus a manager that replaces it, the same pattern as
every other lifecycle in this codebase.** `Order`/`Position`/
`Portfolio` are frozen Pydantic models (ADR-0006) - `OrderManager`/
`PositionManager`/`PortfolioManager` never mutate one in place, they
hold the current value and replace it with a new, validated instance
on every transition, exactly like `ExperimentRegistry` (Phase 14) or
`RiskConfig`/`CapitalState` (Phase 9) before it.

**Every order transition is enforced against an explicit table, not
left as a diagram in a comment.** `ORDER_STATUS_TRANSITIONS`
(`models.py`) is the literal source of truth `OrderManager` checks on
every call - attempting an invalid transition (submitting an
unvalidated order, re-validating a rejected one) raises
`InvalidOrderTransitionError` immediately rather than silently
succeeding.

**The event bus is deliberately simple: synchronous, dispatch-by-exact-
type, no error isolation.** `EventBus.publish()` calls every subscribed
handler in registration order before returning - a handler that raises
propagates straight to the caller, the same as a plain function call
would. This is the right level of complexity for an architecture-
definition phase with a single-threaded demo, not a limitation to code
around; a future engine that needs concurrency can build that on top of
(or instead of) this bus without every other component changing.

**`PaperBroker` is honestly minimal - it fills immediately, in full, at
the requested price.** No slippage, no partial fills, no candle-by-
candle price checking against stop-loss/target the way
`app.trading.backtest.trade_executor` already does for historical
replay. That realism is explicitly the Paper Trading Engine's job (the
next, not-yet-authorized phase) - this phase validates that the
`BrokerInterface` seam works end-to-end, not that fills are realistic.

**Market session is a new, richer abstraction, not a change to the
frozen one.** `app.market_data.market_session` (Phase 4) only
distinguishes PRE_MARKET/OPEN/CLOSED from a single global settings
window, with no lunch break and no holiday concept - exactly the gap
this phase needed to fill for its own purposes. `MarketCalendar`
(`Protocol`) and `ConfigurableCalendar` (its one reference
implementation) take every window and the holiday set as constructor
arguments, with **no NSE-specific default anywhere** - a caller
supplies NSE's actual hours and holidays, this framework never assumes
them.

**The journal and performance monitor both learn everything from the
bus - neither needs to be told about the other, or about the
managers.** `ExecutionJournal.subscribe_to(event_bus)` and
`PerformanceMonitor.__init__(event_bus, ...)` both just subscribe to
the event types they care about; `OrderManager`/`PositionManager`/
`PortfolioManager` publish events and never know or care who's
listening.

`scripts/demo_paper_architecture.py` reuses the existing (frozen)
Indicator/Context/Conditions/Strategy/Risk pipeline for one hand-built
candle snapshot - exactly as `scripts/demo_pipeline.py` already does -
then feeds the resulting decision through the new event-driven pieces,
printing the full sequence (MarketDataReceived → SignalGenerated →
RiskApproved → OrderSubmitted → OrderFilled → PositionUpdated →
PortfolioUpdated) plus the execution journal and performance snapshot -
no real trade executed, no live connectivity used:

```bash
python3 scripts/demo_paper_architecture.py
```

## Paper Trading Engine

`app/runtime/` orchestrates the entire frozen platform - Indicators
through Decision (Phases 5-10), and the event-driven Paper Trading
Architecture (Phase 19) - into a single, replayable runtime loop. It
creates **no** new trading logic: every decision the engine makes is a
call into a package that already owns that decision. Full architecture
diagrams, lifecycle details, failure handling, and the future live
deployment path live in `docs/ENGINE_RUNTIME.md`; this section covers
the key design decisions.

**No business logic belongs in the engine - only orchestration.**
`EventProcessor` re-expresses the exact same orchestration order
`app.trading.backtest.backtest_engine.run_backtest()` (frozen, Phase
11) already uses over historical candles, just through the Phase 19
event-driven pieces instead of a plain in-memory trade list. Indicator/
Context/Conditions/Strategy/Risk/Decision calculations all happen
inside the packages that already own them - never inside
`app/runtime/`.

**Two `Protocol` seams exist specifically so replay-only/synchronous
implementations can be replaced later without the engine changing.**
`MarketDataSource` (`StaticListSource`/`HistoricalReplaySource`, both
in-memory/file-based - no websocket, no Zerodha, no REST API) and
`Scheduler` (`SynchronousScheduler` only, per the CTO brief: "keep
implementation synchronous") both mirror the seam `BrokerInterface`
already established in Phase 19 - a live data feed or an asynchronous
scheduler is a second implementation of the same `Protocol`, not a
rewrite of `RuntimeEngine`.

**Session state is an explicit transition table, not a diagram nobody
enforces.** `SessionController` supports Start/Pause/Resume/Stop/
Replay/End Session exactly as `SESSION_STATE_TRANSITIONS` allows,
mirroring `ORDER_STATUS_TRANSITIONS`'s established pattern (Phase 19).
Because the engine is entirely single-threaded, pausing only ever
takes effect *between* separate `run()` calls, not during one -
`RuntimeEngine.run()` is resumable, continuing from exactly where it
left off since the candle iterator and processed history live on
`self`, not inside one `run()` invocation.

**A stale claim in the (frozen) Phase 19 `EventBus` docstring doesn't
warrant reopening that freeze.** Its docstring suggests subscribing to
`DomainEvent` catches every event regardless of concrete type - but
`EventBus.publish()` actually dispatches by `type(event)` exactly, and
no event is ever published as a bare `DomainEvent`, so that wildcard
subscription would silently never fire. Nothing already-approved in
`app.paper_trading` relies on this claim (verified: `ExecutionJournal`
already subscribes to concrete types individually), so `HealthMonitor`
simply avoids depending on it - subscribing to every concrete event
type itself - rather than treating a never-exercised documentation
inaccuracy as a defect requiring a frozen-package fix.

**`EngineConfig.random_seed` is an honest, currently-unexercised
placeholder.** The CTO brief asks that replay "produce identical
results for the same seed" - true today, but because the entire
pipeline (Indicators through Decision) is inherently deterministic with
no randomness anywhere, not because anything currently consumes the
seed. This is verified empirically in `tests/runtime/test_replay.py`
and documented plainly in `replay.py`'s own docstring, consistent with
this project's practice of flagging unexercised fields rather than
implying capability that doesn't exist yet (e.g. Phase 15's
`SessionConfig` placeholders).

`scripts/demo_runtime_engine.py` replays 100 synthetic candles end to
end, printing session start, replay progress, every signal/order/
portfolio update as it happens, and a final summary - no real trade
executed, no live connectivity used:

```bash
python3 scripts/demo_runtime_engine.py
```

## React Operations Dashboard

`frontend/src/` is an operational control console for the Runtime
Engine (Phase 20) - explicitly not a marketing page or a trading-logic
surface. Full layout, component hierarchy, state management, backend
integration plan, and the future WebSocket migration path live in
`docs/DASHBOARD_GUIDE.md`; this section covers the key design
decisions.

**Every panel reads through exactly one hook; no panel computes a
value the backend didn't already provide.** `useRuntimeStats()`/
`useMarketData()`/`useTradingSignal()`/`useOrders()`/`usePositions()`/
`usePortfolio()`/`useJournal()`/`useHealth()`/`useEngineControls()`
each select one slice of a single `DashboardSnapshot` out of a Zustand
store. "Confidence," for instance, is always `StrategyEvaluation.
strength`/`TradeRecommendation.recommendationStrength` - the backend's
own coarse Strong/Moderate/Weak read (Phases 8/10) - never a
percentage this dashboard invents.

**Zustand, not Redux, and every action is a direct, one-line service
call.** `useDashboardStore` holds one snapshot plus six actions
(`start`/`pause`/`resume`/`stop`/`replay`/`reset`); each is
`() => dashboardService.<method>()` - the store computes nothing and
enforces no transition rules of its own, mirroring the CTO brief's
"Buttons only call backend APIs. No business logic." `EngineControls`'
button enablement mirrors the backend's own `SESSION_STATE_TRANSITIONS`
table (`app.runtime.session_controller`, frozen) purely as a UI
affordance - a disabled button here is advisory, not enforcement; the
service/backend remains the sole authority.

**One service interface, one mock implementation, designed to be
swapped without touching a single component.** `DashboardService`
(`getSnapshot`/`subscribe`/the six actions) is the entire seam.
`MockDashboardService` replays `scripts/dashboard_mock_data.json` (60
synthetic candles, generated with the same weekday-only/warmup-aware
conventions as the backend's own demo scripts - one trade closed
profitably, one left open at the final tick) on a `setInterval`,
reproducing the real `SessionController`'s exact Start/Pause/Resume/
Stop/Replay/Reset semantics. Orders/positions/portfolio/health/
performance are full, cumulative snapshots on every tick, matching how
the real backend's managers always hand back a fresh view rather than
a delta - the journal is the one deliberate exception, since a journal
is inherently an append-only log.

**A real caught bug, fixed before it shipped:** the Journal panel
initially used `flex-direction: column-reverse` to show newest entries
first without re-sorting in JS. A reversed flex container with
`overflow-y: auto` scrolls to reveal its DOM-first (oldest) child when
content overflows, not its last - so the panel silently showed stale
entries pinned at the top once the journal grew past one screen.
Caught via an actual browser screenshot during verification (not by
reading the code), and fixed by reversing the array in JS instead,
keeping a normal `flex-direction: column`.

**Dark, minimal, no animations, no glassmorphism, monospace
throughout.** Every color, spacing value, and radius lives in one file
(`app/theme.css`) as CSS custom properties - no panel hardcodes a
color. The chart is a static placeholder (`ChartPlaceholder`) - no
TradingView, no charting library - clearly labeled as a placeholder
rather than dressed up to look like real data.

**Lint: `oxlint`, not literal ESLint.** The frontend package already
used `oxlint` (a drop-in, Rust-based ESLint-compatible linter)
before this phase - this phase's quality gate runs against the
established tool rather than introducing a second linter alongside it
or ripping out working config to match the brief's literal wording.

`scripts/dashboard_mock_data.json` is generated data, not hand-typed -
a reproducible synthetic replay a real backend integration can later
be validated against side by side. Run the dashboard:

```bash
cd frontend
npm install
npm run dev
```

## Backend Connectivity Layer

Phase 22 replaced `MockDashboardService` with a `RestDashboardService`
implementing the exact same `DashboardService` interface Phase 21
defined - proving out that seam for real. Full endpoint list, request/
response models, polling strategy, error handling, and the migration
path to WebSocket live in `docs/API_GUIDE.md`; this section covers the
key design decisions.

**"No component changes" held exactly because the interface was the
seam.** `services/index.ts`'s one assignment
(`VITE_DASHBOARD_SERVICE=mock|rest`, default `mock`) is the only thing
that decides which implementation backs the whole dashboard - every
Dashboard component, the three-column layout, the Zustand store, and
every selector hook are byte-for-byte unchanged from Phase 21
(verified via `git diff` against the prior commit).

**One background thread per session, not one thread per request.**
`DashboardRuntimeService` (`backend/app/api/dashboard/dashboard_service.py`)
wires the exact same components `app.runtime.startup.start_runtime()`
wires, in the same order, then runs `RuntimeEngine.run()` on a
background OS thread - since it blocks synchronously in a scheduler
loop. `pause()`/`stop()` call `SessionController` directly (the
background thread notices at its next step); `resume()`/`replay()`
spawn a fresh thread, exactly mirroring how `run()` is documented to
be resumable across separate invocations (`docs/ENGINE_RUNTIME.md`).

**An observer, not a new capability, fills the one real display gap.**
Neither `EventProcessor` nor any manager exposes "the most recent
candle/signal/risk decision" as public state - only as transient
events. `DashboardRuntimeService`'s `_EventObserver` subscribes to the
bus the same way `ExecutionJournal`/`PerformanceMonitor`/`HealthMonitor`
already do (frozen, Phases 19/20) - one more observer, not a change to
either package. `latest_recommendation` stays honestly `null`, since no
event carries a `TradeRecommendation` at all - recomputing it
independently would mean re-running the Strategy/Risk/Decision
pipeline outside the package that owns it, exactly the "new trading
logic" this whole engagement has avoided.

**One genuine, previously-latent defect found and fixed - without
touching the frozen package it lived in.** `app.paper_trading.models.
Portfolio.drawdown`/`drawdown_percent` are plain `@property`, and
Pydantic v2 (so FastAPI's JSON responses too) silently omits plain
`@property` from serialization - both fields were invisible to any
REST consumer, despite the frozen `PortfolioPanel` already rendering
them. No endpoint existed before this phase to expose `Portfolio` over
JSON at all, so this was never caught until now. Fixed with
`PortfolioResponse` (`dashboard_models.py`), a subclass in this
phase's own new code that promotes both to `@computed_field @property`,
reusing the parent's exact formula via `super().drawdown` rather than
duplicating it - `app.paper_trading.models` itself is untouched.

**Graceful retry lives entirely in the service layer, since there is
no new UI for it.** The CTO brief's "No component changes" meant no
new connection-status indicator this phase - so `RestDashboardService`
never throws into the (frozen) store and never clears the snapshot on
a failed poll; it logs a descriptive warning and lets the next 1-second
interval tick try again. `services/api/client.ts` distinguishes three
failure modes (`ApiTimeoutError`/`ApiNetworkError`/`ApiHttpError`) so
the log is specific, even though the recovery behavior is identical
either way.

**`reset()` is an honest gap, not a guessed-at mapping.** The brief's
endpoint list has no `POST /api/runtime/reset` - rather than silently
treating Reset as `stop()` or `replay()` (each means something
different), `RestDashboardService.reset()` logs a clear "known gap"
warning and does nothing, leaving the decision to a future phase that
actually adds the endpoint.

```bash
cd backend && uvicorn app.main:app --port 8000   # terminal 1
cd frontend && VITE_DASHBOARD_SERVICE=rest npm run dev   # terminal 2
```

See `scripts/demo_api_connectivity.md` for the full walkthrough,
including verified Start/Pause/Resume against the real backend.

## Zerodha Broker Adapter

`backend/app/brokers/` implements the existing, frozen
`app.paper_trading.broker_interface.BrokerInterface` Protocol against
the real Kite Connect API - broker connectivity only, no new trading
logic. Full architecture, authentication flow, mapping philosophy,
environment variables, error handling, and the migration path to Live
Trading live in `docs/ZERODHA_ADAPTER_GUIDE.md`; this section covers
the key design decisions.

**The same seam `PaperBroker` already proved out, now with a second
implementation.** `docs/PAPER_TRADING_GUIDE.md` documented
`BrokerInterface` as "a future live broker adapter would implement
this same Protocol without `order_manager.py` changing at all" back in
Phase 19 - this phase is that prediction coming true. `PaperBroker` is
untouched; `OrderManager` never knows which broker it holds.

**Reuse the frozen `Order` type directly - there is no separate
"internal Order."** `BrokerInterface.submit_order()`/`cancel_order()`
already mandate `app.paper_trading.models.Order` as both input and
output. A full Kite order response can't become an `Order` on its own,
though - `strategy_name`/`stop_loss`/`target` are this codebase's own
fields, never returned by Zerodha's API - so `mapper.map_kite_order_
update()` takes the *original* internal `Order` and merges Kite's
status/fill data onto it via `model_copy()`, the exact pattern
`OrderManager._transition()` (frozen) already uses for every other
order state change.

**Every Kite SDK call goes through one seam, mirroring
`app.market_data.client.MarketDataClient`'s established pattern.**
`KiteConnectClient` (a `Protocol`) is the only thing
`authentication.py`/`mapper.py`/`zerodha_broker.py` depend on -
`kite_client.py` is the one module in this package that imports
`kiteconnect` at all, and it translates every
`kiteconnect.exceptions.KiteException` subclass into one of six typed
exceptions before anything else ever sees it. Every test in
`tests/brokers/` uses a fake `KiteConnectClient` - zero real API calls
anywhere in this phase.

**Credentials are deliberately independent of `app.kite`'s existing
OAuth login-flow/session database.** That machinery
(`KiteAuthService`/`KiteSessionRepository`, Phase 3) serves a human
logging in through a browser to browse market data - a different
concern from this adapter, which is driven by an already-generated
access token supplied via `ZERODHA_API_KEY`/`ZERODHA_API_SECRET`/
`ZERODHA_ACCESS_TOKEN` environment variables, matching how automated
trading systems actually use Kite Connect day to day. Session
validation is eager: `validate_session()` calls `profile()` (the
cheapest authenticated endpoint) immediately, so an expired token
surfaces as `AuthenticationError` at startup, not on whichever trading
call happens to run first. Kite Connect has no refresh-token concept -
`ZerodhaCredentials.refresh_token` exists because the CTO brief names
it, honestly documented as unused rather than faked.

**One honestly-flagged limitation, surfaced loudly rather than
papered over.** `Order` (frozen) carries no instrument identifier -
`PaperBroker` never needed one, since it simulates a fill in the
abstract. A real Zerodha order needs a trading symbol + exchange to
know *what* to buy. `ZerodhaBroker`'s `trading_symbol_resolver` seam
exists for exactly this; its default implementation raises
`MappingError` immediately, naming the order, rather than silently
guessing wrong - resolving a strategy's intended contract into a real
trading symbol is explicitly Live Trading Mode's job, the next,
not-yet-authorized phase.

`scripts/demo_zerodha_adapter.py` demonstrates authentication, fetching
a profile, mapping an order, mapping a position, and handling an error
- entirely against a fake `KiteConnectClient`, no real credentials, no
real API calls:

```bash
python3 scripts/demo_zerodha_adapter.py
```

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
