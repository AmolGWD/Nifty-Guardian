# NIFTY Guardian — Paper Trading Engine (Runtime) Guide

This guide covers `app/runtime/` (the Paper Trading Engine, Phase 20) -
the orchestration layer that drives the existing, frozen platform
(Indicators, Context, Conditions, Strategy, Risk, Decision - Phases
5-10 - and the event-driven Paper Trading Architecture - Phase 19)
through a replayable candle-by-candle loop. This phase creates **no**
new trading logic: every decision the engine makes is a call into a
package that already owns that decision. It does **not** connect to a
websocket, does **not** talk to Zerodha or any live broker, and has
**no** REST API or UI - only an in-process, synchronous runtime and a
CLI demo script.

## Architecture

```
                    ┌───────────────────┐
                    │  MarketDataSource │  (StaticListSource / HistoricalReplaySource)
                    └─────────┬─────────┘
                              │ next(candle)
                              ▼
   ┌──────────────────────────────────────────────────────┐
   │                     RuntimeEngine                     │
   │  drives one candle at a time through a Scheduler,     │
   │  gated by SessionController's current state           │
   └───────────────────────┬────────────────────────────────┘
                            │ process_candle(candle, history)
                            ▼
   ┌──────────────────────────────────────────────────────┐
   │                    EventProcessor                     │
   │  Receive Market Data                                  │
   │    -> Build IndicatorSnapshot   (Phase 5, frozen)     │
   │    -> Build MarketContext       (Phase 6, frozen)     │
   │    -> Evaluate TradingConditions(Phase 7, frozen)     │
   │    -> Run Strategy Engine       (Phase 8, frozen)     │
   │    -> Run Risk Engine           (Phase 9, frozen)     │
   │    -> Run Decision Engine       (Phase 10, frozen)    │
   │    -> Publish Events            (Phase 19 EventBus)   │
   │    -> Paper Broker              (Phase 19, frozen)    │
   │    -> Portfolio Update          (Phase 19, frozen)    │
   └───────────────────────┬────────────────────────────────┘
                            │ publishes events
                            ▼
                    ┌───────────────┐
                    │   EventBus    │ (Phase 19, frozen)
                    └───┬───────┬───┘
                        │       │
                        ▼       ▼
              ExecutionJournal  PerformanceMonitor   HealthMonitor
                 (Journal)        (Phase 19)          (Phase 20)
```

No indicator, strategy, risk, or decision calculation happens inside
`app/runtime/` - every one of those is a call into the package that
already owns it, mirroring exactly how `app.trading.backtest.
backtest_engine.run_backtest()` (frozen, Phase 11) already orchestrates
the same chain over historical candles. `EventProcessor` is that same
orchestration pattern re-expressed through the event-driven paper
trading pieces (Phase 19) instead of a plain in-memory trade list.
`ExecutionJournal`/`PerformanceMonitor` are never called directly -
both already subscribe to the event bus (Phase 19) and learn
everything from the events `EventProcessor` publishes.

The CTO brief's flow diagram does not name the Decision Engine as its
own box, but selecting among risk-assessed strategy candidates via
`build_trade_recommendation()` (Phase 10) is exactly that step - using
the existing Decision Engine here (rather than inlining an "if
risk_ok: act" check) is reuse, not new trading logic.

Exit checking (stop-loss/target/end-of-day) reapplies the same three
comparisons `app.trading.backtest.trade_executor.check_exit()` already
uses (stop-loss checked before target) - not reused directly, because
that function is tightly coupled to constructing a `BacktestTrade`, a
different shape from `app.paper_trading.models.Position`. Since
`Position` doesn't carry a stop-loss/target (a paper position's target
is a property of the *order* that opened it, not the position itself),
`EventProcessor` tracks the currently open position's stop-loss/target
internally - no change to the frozen `app.paper_trading` package.

## Startup sequence

`app.runtime.startup.start_runtime()` wires every component in the
order the CTO brief names:

1. **Event Bus** - `EventBus()`
2. **Managers** - `PositionManager`, `PortfolioManager`, `OrderManager`
3. **Paper Broker** - `PaperBroker()`
4. **Portfolio** - `SessionController`, `ExecutionJournal` (subscribed),
   `PerformanceMonitor`, `HealthMonitor`, `EventProcessor`
5. **Runtime Engine** - `RuntimeEngine`, backed by a
   `SynchronousScheduler`

It returns a `RuntimeContext` - a plain `@dataclass` bundling every
wired instance (not a Pydantic model: these are stateful services, not
immutable domain values) - so callers (the demo script, tests) don't
have to repeat this wiring themselves. `risk_config` defaults to
`RiskConfig()` and `strategy_registry` defaults to `default_registry()`
when omitted.

## Runtime lifecycle

```
NotStarted ──start()──► Running ──pause()──► Paused
                │                                │
                │◄────────resume()───────────────┘
                │
                ├──stop()──► Stopped ──end_session()──► Ended
                │                │                        │
                │                └──────replay()───────────┤
                │                                          │
                └──────────────────end_session()───────────┘
                                                            │
                                              Ended ◄──replay()── (fresh run)
```

`SessionController` enforces this exactly via an explicit transition
table (`SESSION_STATE_TRANSITIONS`), mirroring
`app.paper_trading.models.ORDER_STATUS_TRANSITIONS`'s pattern - a table
`SessionController` checks on every call, not a diagram nobody
enforces. `replay()` is the one action that re-enters `Running` from a
terminal-ish state (`Stopped`/`Ended`) without constructing a new
`SessionController` - distinct from `start()`, which only ever works
from `NotStarted`.

### Why Pause/Resume works for a synchronous engine

`RuntimeEngine` is entirely single-threaded: nothing else can call
`pause()` *while* `run()` is executing, since `run()` is a blocking
call on the same thread. Pausing therefore only ever takes effect
*between* separate `run()` invocations:

- `_step()` returns `False` immediately whenever the session's state is
  not `Running` - this hands control back to the caller.
- `run()` is resumable: calling it again after an external `pause()`
  call (from, say, a UI button handler or a test) auto-resumes the
  session and continues from exactly where it left off, since the
  candle iterator and processed history live on `self`, not inside one
  `run()` call.
- Calling `run()` again after `Stopped`/`Ended` is a no-op - call
  `replay()` (on the `SessionController`) for a fresh run instead of
  calling `run()` again, since the candle iterator behind a `Stopped`/
  `Ended` engine has already been exhausted or intentionally halted.

## Shutdown sequence

`app.runtime.shutdown.shutdown_runtime()`:

1. **Flush journal** - reads `ExecutionJournal.all_entries()`. In-memory
   this phase (no external store), so "flushing" means reading the
   final in-memory state rather than writing anywhere external.
2. **Stop scheduler** - implicit: `SynchronousScheduler.run()` has
   already returned control to `RuntimeEngine.run()` by the time
   shutdown is called (there is no separate scheduler handle to
   signal), so this step is folded into closing the session.
3. **Close session** - transitions `Running`/`Paused` → `Stopped` →
   `Ended`, matching whatever state the run left the session in.
4. **Print summary** - portfolio, performance, and health snapshots,
   printed via `_print_summary()`.

It returns a `ShutdownSummary` (`@dataclass`) bundling the journaled
entries and final snapshots - computed nothing new, every figure
already exists on `PortfolioManager`/`PerformanceMonitor`/
`HealthMonitor`.

## Replay mode

`app.runtime.replay.run_replay()` is the single-call convenience
wrapper: `start_runtime()` → `context.engine.run()` →
`shutdown_runtime()`, returning both the `RuntimeContext` and the
`ShutdownSummary`.

**Determinism** here means what it means for every other replay-like
component in this codebase (Grid Search, Walk-Forward, Monte Carlo):
the same inputs (candles, config) always produce the same sequence of
events and the same final state. `EngineConfig.random_seed` is included
per the CTO brief and reserved for a future perturbation that needs
real randomness - today's pipeline
(Indicators/Context/Conditions/Strategy/Risk/Decision) never draws from
an RNG, so "same seed → identical results" holds trivially from the
pipeline's own inherent determinism, not because anything currently
consumes the seed. This is an honest, flagged placeholder, verified
empirically (and covered by `tests/runtime/test_replay.py`): running
`run_replay()` twice against identical candles produces identical
`final_portfolio.total_equity`, `orders_submitted` counts, and
processed-candle counts.

### Replay speed

`ReplaySpeed` (`1x`/`2x`/`5x`/`10x`/`Unlimited`) controls the wall-clock
delay between processed candles via `sleep_seconds_for()` - `Unlimited`
always means zero delay regardless of the candle interval, i.e. process
as fast as possible. This is purely a pacing knob for a human watching
the demo script; it has no effect on what gets computed or in what
order.

## Market data sources

`MarketDataSource` (`Protocol`: `__iter__`, `__len__`) has two
implementations this phase, both purely in-memory/file-based:

- `StaticListSource` - wraps an already-in-memory `list[Candle]`
  directly (what the demo script and most tests use).
- `HistoricalReplaySource` - loads a CSV via the existing (frozen)
  `app.trading.backtest.loader.load_candles_from_csv` - no CSV parsing
  is reimplemented here.

No websocket, no Zerodha, no REST API anywhere in this module. A
future live source would be a third implementation of the same
`Protocol` - the same seam `app.paper_trading.broker_interface.
BrokerInterface` already established for brokers.

## Scheduler

`Scheduler` (`Protocol`: `run(step, *, delay_seconds)`) has one
implementation this phase, `SynchronousScheduler`, per the CTO brief
("keep implementation synchronous"). It loops calling `step()` until it
returns `False`, sleeping `delay_seconds` between calls when positive.
`sleep_fn` is injectable (defaults to `time.sleep`) so tests never wait
on a real clock. The `Protocol` seam exists specifically so an
asynchronous scheduler (awaiting a coroutine step, or driven by an
event loop instead of a plain `while` loop) can replace it later
without `RuntimeEngine` changing at all.

## Health monitoring

`HealthMonitor` tracks exactly what the CTO brief asks for: processed
candles, average processing latency, engine uptime, events published,
orders generated, and current session state - purely from what the
engine itself observes (`record_candle_processed()`, called by
`RuntimeEngine` after every `EventProcessor.process_candle()` call) and
what the event bus reports. `current_state` is read directly from
`SessionController`, never duplicated.

`HealthMonitor` subscribes to every concrete event type individually
(`MarketDataReceivedEvent`, `SignalGeneratedEvent`, `RiskApprovedEvent`,
`OrderSubmittedEvent`, `OrderPartiallyFilledEvent`, `OrderFilledEvent`,
`OrderCancelledEvent`, `OrderRejectedEvent`, `PositionUpdatedEvent`,
`PortfolioUpdatedEvent`) rather than to `DomainEvent` itself, mirroring
`ExecutionJournal`'s actual approach. This is a deliberate departure
from a stale claim in `app.paper_trading.event_bus`'s own docstring,
which suggests subscribing to `DomainEvent` catches every event
regardless of concrete type - `EventBus.publish()` actually dispatches
by `type(event)` exactly, and no event is ever published as a bare
`DomainEvent` instance, so a wildcard subscription to the base class
would silently never fire. `app.paper_trading` is frozen this phase and
nothing there actually relies on that docstring's claim (a real defect
would need flagging and a minimal fix; a stale docstring describing a
never-exercised capability does not), so `HealthMonitor` simply avoids
depending on it.

## Failure handling and recovery

This phase's failure model is intentionally minimal, matching its
scope (a synchronous, in-process, no-network runtime):

- **Invalid session transitions** (e.g. calling `pause()` before
  `start()`) raise `InvalidSessionTransitionError` immediately - the
  caller sees the failure at the exact call site, not several steps
  later.
- **Data source exhaustion** is not a failure: `RuntimeEngine._step()`
  catches `StopIteration` from the candle iterator and treats it the
  same as reaching `EngineConfig.maximum_candles` - both call
  `_maybe_auto_stop()`, which transitions the session to `Stopped` only
  if `auto_stop_on_completion` is `True`, otherwise leaving the session
  `Running` with no more candles to process (a caller can inspect
  `engine.processed_count` against `len(market_data_source)` to detect
  this).
- **Recovery from a pause** is `resume()` followed by `run()` (or just
  `run()`, which resumes automatically) - no state is lost, since
  `RuntimeEngine` keeps its candle iterator and processed history on
  `self` across `run()` calls.
- **There is no crash-recovery/persistence story this phase** - every
  component (`EventBus`, managers, journal) is in-memory only, the same
  established pattern as `app.research.experiment_registry.
  ExperimentRegistry`. A process restart loses all runtime state; that
  is an explicit, known limitation of this phase, not an oversight -
  persistence is a live-deployment concern (see below), and this phase
  has no live deployment yet.

## Future live deployment

Nothing in this phase's design assumes replay is the *only* mode the
engine will ever run in - the two `Protocol` seams
(`MarketDataSource`, `Scheduler`) exist specifically so a live
deployment can slot in without changing `RuntimeEngine`,
`EventProcessor`, or anything downstream:

- A **live market data source** would be a third `MarketDataSource`
  implementation - e.g. one backed by a websocket or Kite's live feed -
  yielding `Candle`s as they arrive instead of iterating a pre-loaded
  list. `EventProcessor.process_candle()` doesn't know or care whether
  a candle came from a CSV file, an in-memory list, or a live tick.
- An **asynchronous scheduler** would be a second `Scheduler`
  implementation, replacing the synchronous `while` loop with an event
  loop or a coroutine-driven step function - `RuntimeEngine` calls
  `scheduler.run(self._step, delay_seconds=...)` through the `Protocol`
  either way.
- A **live broker** is already a solved seam from Phase 19:
  `BrokerInterface` (`submit_order`/`cancel_order`) has exactly one
  implementation today (`PaperBroker`), and a live adapter is a second
  implementation of the same two methods - every other Phase 19/20
  component is unchanged, because none of them know or care which
  `BrokerInterface` implementation they were given.
- `TradingSessionMode.LIVE_HOURS` (`engine_config.py`) is an honest,
  currently-unimplemented placeholder for gating entries on a real
  session clock instead of treating every candle as tradeable - there
  is no live feed yet to gate, so nothing in this phase implements it
  beyond the name.
- Live deployment would also need to address the persistence gap noted
  above (crash recovery, restart-safe journal/portfolio state) and real
  partial-fill/async order confirmation handling (`PaperBroker` always
  fills synchronously and completely; a live broker legitimately can't
  make that guarantee) - both explicitly out of scope for this phase,
  consistent with `docs/PAPER_TRADING_GUIDE.md`'s own migration-path
  notes for `BrokerInterface`.

## Demo

`scripts/demo_runtime_engine.py` replays 100 synthetic historical
candles end to end - session start, replay progress, signals, orders,
portfolio updates, and a final summary - no real trade executed, no
live connectivity used:

```bash
python3 scripts/demo_runtime_engine.py
```
