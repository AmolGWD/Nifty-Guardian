# NIFTY Guardian v2 — System Architecture

This document describes the architecture of the rebuilt backend
(`backend/app/`, branch `feature/nifty-guardian-v2`) as of Phase 10
(Decision Engine). It is a living reference for engineers joining the
project - it should be updated whenever a future phase changes a
package boundary, not left to drift from the code.

---

## 1. Overview

### Purpose

NIFTY Guardian generates high-conviction **paper-trading** signals for
NIFTY weekly options, using live Zerodha Kite market data. It is
explicitly not an automated real-money trading system - there is no
broker order placement anywhere in this codebase, at any phase.

### Design philosophy

The system is built as a strict pipeline of small, independently
testable stages, each answering exactly one question:

- What do the numbers say? (Indicators)
- What kind of market is this? (Market Context)
- Is trading currently allowed? (Trading Conditions)
- What would a given strategy do here? (Strategy Engine)
- How much risk would that take? (Risk Engine)
- Should any of that be acted on? (Decision Engine)

No stage answers more than one of these questions, and no stage can
see further downstream than the one that consumes its output. This is
a direct, deliberate reaction to the pre-rebuild codebase (still
visible on `debug/signal-runtime`), where indicator calculation,
scoring, and the BUY/SELL decision were fused into one
`guardian_engine.py` call chain that was difficult to test, debug, or
extend safely, and which - by having no clear boundary anywhere -
ended up with real broker credentials committed into git history.

### Guiding principles

- **Determinism.** Every stage is a pure function of its declared
  inputs. No hidden state, no randomness, no wall-clock reads inside
  business logic (timestamps are always passed in explicitly).
- **Immutability.** Every domain output is a frozen Pydantic model.
  Once built, a result cannot be mutated by a downstream consumer.
- **Independent gates, not cascading approval.** Strategy validity,
  trading permission, and risk acceptability are evaluated
  independently of each other; only the Decision Engine combines them.
- **No premature decisions.** No BUY/SELL, no numeric confidence score,
  anywhere below the Decision Engine (see ADR-0002).
- **Broker isolation.** Exactly two files import `kiteconnect`,
  both behind a `Protocol`; everything else operates on normalized,
  broker-agnostic data (see ADR-0003).
- **Verify, don't assert.** Every phase in this rebuild has confirmed
  its architectural claims (import boundaries, absence of forbidden
  terms) with `grep`, not just design intent - and confirmed behavior
  with real test runs, not just code review.

---

## 2. High Level Architecture

```
Market Data
      ↓
Indicators
      ↓
Market Context
      ↓
Trading Conditions
      ↓
Strategy Engine
      ↓
Risk Engine
      ↓
Decision Engine
      ↓
Paper Trading (future)
      ↓
Analytics (future)
```

Each arrow is a one-way data dependency: the layer below consumes the
frozen output model of the layer above (plus, in a few cases, one
sibling input - Trading Conditions also reads Market Context; Risk
reads Strategy's output; Decision reads Strategy, Risk, and Trading
Conditions together). No layer imports anything from a layer above it,
and no layer skips ahead to call a layer two steps below it directly -
every hop goes through the model in between.

Authentication (`app.kite`) and raw Kite access (`app.market_data`) sit
beside this pipeline, not inside it - they produce the `Candle` data
that seeds Indicators, but carry no trading logic themselves.

---

## 3. Package Structure

### `app.api`

FastAPI routes only (`app/api/routes/health.py`, `kite_auth.py`,
`market_data.py`). Wires HTTP requests to services in `app.kite` and
`app.market_data` via dependency injection (`Depends(...)`). Contains
no business logic of its own - a route handler calls a service method
and translates its result/exception into an HTTP response.

### `app.core`

Cross-cutting application concerns with no trading-domain knowledge:
`config.py` (Pydantic Settings, loaded from environment variables),
`logging.py` (stdlib logging configuration), `database.py` (SQLAlchemy
engine/session/`get_db` dependency), `repository.py` (generic
`Repository[ModelType]` base class), `security.py` (Fernet encryption
for secrets at rest).

### `app.kite`

Zerodha authentication and session management: `client.py` builds the
real KiteConnect SDK client; `service.py`'s `KiteAuthService` drives
the login/session-exchange flow behind `KiteClientProtocol`; `models.py`
defines `KiteSession` (encrypted access token); `repository.py` persists
and retrieves sessions. This is the only package that ever writes a
Kite access token to the database.

### `app.market_data`

Normalizes all market data into plain Pydantic schemas
(`SpotPrice`, `Candle`, `Instrument`, `OptionContract` in `schemas.py`)
so the rest of the application never touches a raw Kite SDK response.
`client.py`'s `MarketDataClient` Protocol is the only other seam where
`kiteconnect` is imported (implemented by `KiteMarketDataClient`).
`instrument_lookup.py`, `spot_price.py`, `candles.py`, `expiry.py`,
`option_chain.py` build on that client; `market_session.py` is pure
clock logic with no Kite dependency at all.

### `app.trading.indicators`

Pure technical-indicator math (EMA, RSI, VWAP, SuperTrend, Volatility/
ATR, Put Call Ratio, Open Interest Analysis, Trend Direction, Volume
Analysis) over `app.market_data.schemas.Candle`. No indicator imports
another; `engine.py` composes all nine into one frozen
`IndicatorSnapshot`. Zero Kite/FastAPI/SQLAlchemy/HTTP dependency.

### `app.trading.context`

Converts an `IndicatorSnapshot` (plus `MarketSessionStatus`, supplied
separately since it's wall-clock-derived, not indicator-derived) into
an objective, deterministic `MarketContext`: Trend, Momentum,
Volatility, Volume Strength, Market Bias, Option Chain Bias, Session
State, Overall Market State. No signals, no BUY/SELL, no confidence.

### `app.trading.conditions`

Answers one question: is trading currently *permitted*? Nine
independent evaluators (market open, opening range, no-trade zone,
session validation, expiry day, gap, position guard, cooldown,
liquidity) compose into a frozen `TradingConditions`. Does not decide
BUY/SELL - only whether a strategy should be considered at all right
now.

### `app.trading.strategy`

A plugin architecture: strategies implement the `Strategy` Protocol
(`base.py`), register with a `StrategyRegistry` (`registry.py`), and
`run_strategies()` (`engine.py`) executes every registered strategy
against the same `IndicatorSnapshot`/`MarketContext`/`TradingConditions`
and returns their `StrategyEvaluation`s - no comparison or ranking here.
One concrete strategy, `EMABreakoutStrategy`, is implemented.

### `app.trading.risk`

Evaluates trade risk **independently of strategy validity**: position
sizing, stop-loss, target, reward/risk, and four risk-limit gates
(daily loss, max trades per day, capital exposure, max concurrent
positions) compose into a frozen `RiskAssessment`. Does not approve or
reject a trade - only whether it would be within risk limits.

### `app.trading.decision`

The one package allowed to combine `StrategyEvaluation`,
`RiskAssessment`, and `TradingConditions` together into a single
`TradeRecommendation`. Selects the strongest qualifying candidate
(deterministically) and reports whether it's actionable right now. No
trade execution, no position management, no P&L.

---

## 4. Layer Responsibilities

### Indicators

- **Inputs:** `list[Candle]`, option-chain OI totals, price/OI deltas.
- **Outputs:** `IndicatorSnapshot` (frozen).
- **Responsibilities:** Compute EMA, RSI, VWAP, SuperTrend, ATR/ATR%,
  PCR, Open Interest signal, Trend Direction, Volume Analysis, and
  expose the current candle close (`close_price`).
- **Forbidden:** Any classification, permission, strategy, or decision
  logic; any Kite/FastAPI/SQLAlchemy/database import; any BUY/SELL or
  confidence concept.

### Market Context

- **Inputs:** `IndicatorSnapshot`, `MarketSessionStatus`.
- **Outputs:** `MarketContext` (frozen).
- **Responsibilities:** Classify Trend, Momentum, Volatility, Volume
  Strength, Market Bias, Option Chain Bias, and one composed Overall
  Market State - a description of the market, nothing more.
- **Forbidden:** Any signal, entry/exit logic, confidence score, or
  reference to trading permission/risk/strategy.

### Trading Conditions

- **Inputs:** `MarketSessionStatus`, current timestamp, `MarketContext`,
  configuration values (market open/close, opening range minutes,
  no-trade zone minutes, expiry/gap/cooldown/liquidity parameters).
- **Outputs:** `TradingConditions` (frozen).
- **Responsibilities:** Determine whether trading is currently
  *permitted* - session validity, timing windows, expiry-day rules,
  and framework/stub gates for gap/position/cooldown/liquidity where
  no real data source exists yet.
- **Forbidden:** Any BUY/SELL decision, confidence score, or
  broker-specific logic; no FastAPI, no database.

### Strategy Engine

- **Inputs:** `IndicatorSnapshot`, `MarketContext`, `TradingConditions`.
- **Outputs:** `list[StrategyEvaluation]` (one per registered strategy;
  each frozen).
- **Responsibilities:** Let each registered strategy independently
  judge whether its own setup is present, reporting a categorical
  `direction` (Long/Short/None) and `strength` (Strong/Moderate/Weak).
- **Forbidden:** Comparing or choosing between strategies; a final
  BUY/SELL decision; a numeric confidence score; broker logic; FastAPI;
  a database.

### Risk Engine

- **Inputs:** One `StrategyEvaluation` (for its `direction` only),
  `entry_price`, `atr`, `RiskConfig`, `CapitalState`.
- **Outputs:** `RiskAssessment` (frozen).
- **Responsibilities:** Position sizing, stop-loss/target (ATR-based),
  reward/risk ratio, and four independent risk-limit gates (daily loss,
  max trades/day, capital exposure, max concurrent positions).
- **Forbidden:** Reading `StrategyEvaluation.valid` to influence
  `risk_ok`; approving or rejecting a trade outright; broker logic;
  FastAPI; a database.

### Decision Engine

- **Inputs:** `list[StrategyCandidate]` (each pairing a
  `StrategyEvaluation` with its own `RiskAssessment`), `TradingConditions`.
- **Outputs:** `TradeRecommendation` (frozen).
- **Responsibilities:** Select the strongest candidate whose strategy
  is valid *and* whose risk is ok, deterministically; gate
  `recommended` on `TradingConditions.can_trade`; explain the outcome
  via `reasons`/`warnings`.
- **Forbidden:** Executing a trade; maintaining a position; updating
  P&L; introducing a numeric confidence score; broker logic; FastAPI;
  a database.

---

## 5. Dependency Rules

```
app.trading.indicators   -> app.market_data.schemas (Candle) only
app.trading.context      -> app.trading.indicators, app.market_data.market_session
app.trading.conditions   -> app.trading.context, app.market_data.market_session
app.trading.strategy     -> app.trading.indicators, app.trading.context, app.trading.conditions
app.trading.risk         -> app.trading.strategy (StrategyDirection/StrategyEvaluation only)
app.trading.decision     -> app.trading.strategy, app.trading.risk, app.trading.conditions
```

No package under `app.trading` imports `app.kite`, `app.api`,
`app.core.database`, `fastapi`, `sqlalchemy`, or `kiteconnect` - this is
re-verified by grep at the end of every phase, not assumed to still
hold from a previous phase.

Explicitly, and by design:

- **Indicators know nothing about Kite.** `app.trading.indicators`
  imports only `app.market_data.schemas.Candle`, a plain normalized
  model - never `app.kite`, never `kiteconnect`.
- **Strategy knows nothing about FastAPI.** `app.trading.strategy` has
  no `fastapi` import anywhere; it is driven directly by
  `run_strategies()` with plain function arguments, testable with zero
  HTTP machinery.
- **Risk knows nothing about Zerodha.** `app.trading.risk` has no
  `app.kite` or `kiteconnect` import; its only cross-package
  dependency is `app.trading.strategy.models` for `StrategyDirection`.
- **Decision owns recommendation generation.** `app.trading.decision`
  is the only package that combines `StrategyEvaluation.valid` and
  `RiskAssessment.risk_ok` into one outcome - no earlier package is
  allowed to do this, and no later package (Paper Trading) is meant to
  redo it.

---

## 6. Data Flow

How one market snapshot becomes a recommendation, end to end
(see `scripts/demo_pipeline.py` for a runnable version):

1. **Candles arrive** as `list[Candle]` (from `app.market_data`, backed
   by live Kite data in production, or hand-built sample data in the
   demo script/tests).
2. **`calculate_indicator_snapshot(candles, ...)`** computes all nine
   indicators plus the latest close price, producing one
   `IndicatorSnapshot`.
3. **`build_market_context(snapshot, session_state)`** classifies that
   snapshot (plus the current `MarketSessionStatus`) into one
   `MarketContext` - Trend, Momentum, Volatility, Volume Strength,
   Market Bias, Option Chain Bias, Overall Market State.
4. **`build_trading_conditions(...)`** takes the session state, the
   current timestamp, the `MarketContext`, and configuration values,
   and produces one `TradingConditions` - whether trading is currently
   permitted, and why not if it isn't.
5. **`run_strategies(registry, snapshot, market_context,
   trading_conditions)`** runs every registered strategy (today, just
   `EMABreakoutStrategy`) against the same three inputs, returning one
   `StrategyEvaluation` per strategy.
6. **`build_risk_assessment(strategy_evaluation=evaluation,
   entry_price=..., atr=..., config=..., capital_state=...)`** runs
   once per strategy evaluation (each needs its own risk assessment,
   since stop-loss/target placement depends on that strategy's own
   `direction`), producing one `RiskAssessment` per candidate.
7. Each `(StrategyEvaluation, RiskAssessment)` pair is wrapped into a
   `StrategyCandidate`.
8. **`build_trade_recommendation(candidates=..., trading_conditions=...)`**
   selects the strongest candidate whose strategy is valid and whose
   risk is ok, gates the result on `TradingConditions.can_trade`, and
   returns one `TradeRecommendation` - the end of this phase's pipeline.

No step above touches a database, an HTTP request, or the KiteConnect
SDK - every one of them is a plain function call over frozen Pydantic
models.

---

## 7. Extension Points

### Add a new strategy

Implement the `Strategy` Protocol (`app/trading/strategy/base.py`) in a
new module under `app/trading/strategy/` - a `name` attribute and an
`evaluate(snapshot, context, conditions) -> StrategyEvaluation` method.
Register it in `default_registry()` (`registry.py`). No change needed
to `engine.py`, `registry.py`, or any existing strategy. Write unit
tests against the same `tests/trading/strategy/helpers.py` factories
used by `EMABreakoutStrategy`'s tests.

### Add a new broker

Implement the relevant Protocol(s) for real:
`app.kite.service.KiteClientProtocol` for authentication, and/or
`app.market_data.client.MarketDataClient` for market data. Nothing
under `app.trading` needs to change - it never imports a broker SDK or
a Protocol implementation directly, only the normalized output types
(`Candle`, `IndicatorSnapshot`, ...). A second broker would likely mean
a new factory function alongside `app.kite.client.build_kite_client()`
and `KiteMarketDataClient`, selected by configuration.

### Add a new indicator

Add a new pure function/module under `app/trading/indicators/`
(matching the existing one-file-per-indicator, no-cross-imports
pattern), add its field(s) to `IndicatorSnapshot`
(`app/trading/indicators/models.py`), and wire it into
`calculate_indicator_snapshot()` (`engine.py`). Add a dedicated test
file with hand-computed expected values, following the pattern in
`tests/trading/indicators/`. If a downstream package (Context,
Strategy) needs the new field, that is a separate, explicitly-reviewed
change to that package - not assumed automatically.

### Add a new risk rule

Add a new evaluator module under `app/trading/risk/` (a pure function
taking explicit primitives, following the pattern of
`daily_loss_limit.py`/`max_trades_per_day.py`/etc.), add any new
required configuration field to `RiskConfig` or `CapitalState`
(`models.py`), add a new `RiskRejectionReason` member if it's a
pass/fail gate, and wire it into `build_risk_assessment()`
(`engine.py`) - both computing the new evaluator's result and adding it
to `rejection_reasons` when it fails. Add a dedicated test file
alongside the existing ones in `tests/trading/risk/`.

---

## 8. Testing Strategy

### Unit tests (current, `backend/tests/`)

Every package under `app.trading` is tested in complete isolation with
plain constructed inputs - no fakes, no mocks, no database, no HTTP
server. Indicator/context/conditions/risk math is checked against
hand-computed expected values wherever the algorithm makes that
practical (SuperTrend is checked by behavior instead, given how many
interacting steps its recursive band-flipping algorithm has). Every
frozen model has a dedicated immutability test
(`pytest.raises(ValidationError)` on attempted mutation). `app.kite`
and `app.market_data` are tested against fakes implementing their
Protocols (`FakeMarketDataClient`, a fake Kite client), never a real
network call. 203 tests as of Phase 10 (`pytest tests/ -v`).

### Integration tests (not yet built)

None exist yet that exercise more than one `app.trading` package
wired together against a real (not sandboxed) FastAPI `TestClient` and
a real SQLite database - today's tests either stay within one
`app.trading` package or exercise `app.kite`/`app.market_data` against
fakes. A future integration suite would assemble the full pipeline
(Section 6) behind an actual HTTP endpoint and assert the end-to-end
`TradeRecommendation` for a given fixture data set - closer to what
`scripts/demo_pipeline.py` does manually, but via `pytest` and the real
API layer.

### Future Paper Trading tests

Once Paper Trading (position management, P&L, trade journal) exists,
it will need: position lifecycle tests (open, track, close a paper
position against a `TradeRecommendation`), P&L calculation tests
against hand-computed values (same discipline as the indicator tests),
and persistence tests against a real (test) database, following the
existing `tests/test_repository.py` pattern.

### Future Live Trading tests

Not planned - this application does not place real broker orders, and
no phase in the roadmap (Section 10) introduces that capability. If it
is ever added, it would need, at minimum: a paper-vs-live mode toggle
that defaults to paper, tests confirming the toggle cannot be silently
bypassed, and tests against a broker sandbox/fake that never touches a
real account by default.

---

## 9. ADR Summary

Full text lives in `docs/adr/`; index in `docs/adr/README.md`.

- **[ADR-0001](adr/0001-layered-trading-domain-architecture.md) -
  Layered trading domain architecture.** The trading domain is built as
  a strict pipeline of independent packages (Indicators → Context →
  Conditions → Strategy → Risk → Decision), each with one immutable
  frozen output and zero knowledge of packages downstream of it,
  replacing the pre-rebuild's tangled, dictionary-passing
  `guardian_engine.py` chain. Verified by grep at every phase boundary,
  not just asserted by design.

- **[ADR-0002](adr/0002-no-buy-sell-or-confidence-scoring-until-the-decision-engine.md) -
  No BUY/SELL or confidence scoring until the Decision Engine.** No
  package below `app.trading.decision` may emit a BUY/SELL-style
  decision or a numeric confidence percentage; classification packages
  emit categorical enums, Strategy emits categorical direction/strength,
  Risk emits a boolean gate plus concrete figures, and only Decision
  combines these into one recommendation - still with no numeric score.

- **[ADR-0003](adr/0003-broker-isolation-via-protocol-seams.md) -
  Broker isolation via Protocol seams.** Every real KiteConnect SDK
  call is confined to two files (`app.kite.client`,
  `app.market_data.client.KiteMarketDataClient`), each hidden behind a
  Protocol; nothing under `app.trading` imports `app.kite` or
  `kiteconnect` at all, so every trading-domain test runs with zero
  network access and zero real credentials.

- **[ADR-0004](adr/0004-plugin-architecture-for-strategies.md) -
  Plugin architecture for strategies.** `app.trading.strategy` defines
  a `Strategy` Protocol and a `StrategyRegistry`; `run_strategies()`
  executes every registered strategy without comparing or choosing
  between them (Decision Engine's job). Adding a second strategy is a
  new file plus one registration line, no change to existing code.

- **[ADR-0005](adr/0005-risk-evaluated-independently-of-strategy-validity.md) -
  Risk evaluated independently of strategy validity.** `RiskAssessment.risk_ok`
  reflects only its own four risk-limit gates and never reads
  `StrategyEvaluation.valid`; a strategy's `direction` is used only to
  place stop-loss/target on the correct side of `entry_price`. The
  Decision Engine is the first and only layer allowed to combine both
  gates together.

- **[ADR-0006](adr/0006-immutable-frozen-domain-models.md) -
  Immutable, frozen domain models everywhere.** Every domain output
  (`IndicatorSnapshot`, `MarketContext`, `TradingConditions`,
  `StrategyEvaluation`, `RiskAssessment`, `TradeRecommendation`, ...) is
  a frozen Pydantic model with a dedicated immutability test, replacing
  the pre-rebuild's mutable, untyped `dict`-passing between stages.

- **[ADR-0007](adr/0007-minimal-flagged-gap-fixes-to-approved-phases.md) -
  Minimal, flagged gap-fixes to already-approved phases.** When a later
  phase finds a genuine gap in earlier approved work (Phase 4's missing
  `create_all()` call, Phase 6's missing ATR, Phase 8's missing
  `close_price`, Phase 9's missing `entry_price`/`atr`), the fix is the
  smallest closing change, prominently flagged in code, README, and the
  phase summary - never silently expanded scope, and never a dead
  parameter kept just for literal interface compliance.

---

## 10. Future Roadmap

Per the current, CTO-reviewed roadmap (see root `README.md`'s
"Roadmap" section for the full numbered list):

- **Paper Trading (Phase 11).** Position management, P&L tracking, and
  a trade journal, built on top of `TradeRecommendation` - the first
  phase that actually records a position, still with no real broker
  order placement.
- **Analytics (Phase 12).** A performance dashboard, statistics, and
  reports over the paper-trading journal.
- **React dashboard (Phase 13).** Live market view, signal cards,
  history, and charts in the frontend, consuming the backend API.
- **Telegram notifications, deployment, production hardening
  (Phase 14).** Alerting on new recommendations, containerized
  deployment, and the operational hardening (secrets management,
  monitoring, exchange holiday calendar, etc.) needed before any real
  usage beyond local development.
