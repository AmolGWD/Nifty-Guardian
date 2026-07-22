# NIFTY Guardian — Paper Trading Architecture Guide

This guide covers `app/paper_trading/` (the Paper Trading Architecture,
Phase 19) - the complete event-driven design for paper trading. This
phase defines interfaces, models, and workflows; it does **not**
execute trades and does **not** connect to Zerodha or any live market
data. The continuous replay/live loop that would actually drive these
pieces together against real or replayed data is the Paper Trading
Engine - a later, separately-reviewed phase this one explicitly stops
short of.

## Architecture

Every domain object (`Order`, `Position`, `Portfolio`) is a frozen
Pydantic model, the same discipline as every other domain package
(ADR-0006) - a "lifecycle" here means the same thing it has meant
since `Experiment`/`ExperimentResult` (Phase 14): the value itself
never mutates in place. `OrderManager`/`PositionManager`/
`PortfolioManager` each hold the *current* state and *replace* it with
a new, validated instance on every transition; nothing ever does
`order.status = OrderStatus.FILLED`.

```
                         ┌─────────────┐
                         │  EventBus   │◄──────────────┐
                         └──────┬──────┘                │
              publishes events  │        subscribes      │
     ┌───────────────┬──────────┼───────────┬────────────┼──────────────┐
     ▼               ▼          ▼           ▼            ▼              ▼
MarketData      OrderManager  Position   Portfolio  ExecutionJournal  Performance
(external)      + PaperBroker  Manager    Manager    (records every    Monitor
                                                       event)          (computes
                                                                        metrics from
                                                                        events)
```

`OrderManager` is the only component that calls into `BrokerInterface`
(`PaperBroker`, this phase's only implementation) and publishes the
resulting order events. `PositionManager` and `PortfolioManager` are
independent of each other's internals - `PortfolioManager` reads
`PositionManager.open_positions()`/`closed_positions()` to compute
equity, rather than duplicating position bookkeeping.

## Event flow

`docs/PAPER_TRADING_GUIDE.md`'s own demo (`scripts/
demo_paper_architecture.py`) drives one full sequence, reusing the
existing (frozen) Indicator/Context/Conditions/Strategy/Risk pipeline
for the first three steps exactly as `scripts/demo_pipeline.py`
already does, then feeding the result through the new pieces:

```
MarketDataReceived
        │  (existing Indicator/Context/Conditions engines run here)
        ▼
SignalGenerated          (existing Strategy Engine's StrategyEvaluation)
        │
        ▼
RiskApproved              (existing Risk Engine's RiskAssessment)
        │
        ▼
OrderSubmitted            (OrderManager.submit() -> PaperBroker)
        │
        ▼
OrderFilled                (PaperBroker's simulated fill)
        │
        ▼
PositionUpdated           (PositionManager.open_position())
        │
        ▼
PortfolioUpdated          (PortfolioManager.snapshot())
```

`ExecutionJournal` and `PerformanceMonitor` both subscribe to the bus
independently and observe this same sequence without either of the
managers above needing to know they exist - a manager only ever
publishes an event; whatever else happens to be listening is not its
concern.

## Order lifecycle

```
        NEW
         │
         ▼
     VALIDATED ────────────► REJECTED
         │                      ▲
         ▼                      │
     SUBMITTED ─────────────────┤
      │    │    │               │
      ▼    ▼    ▼               │
  FILLED  PARTIALLY   CANCELLED ┘
          _FILLED
             │  │
             ▼  ▼
         FILLED  CANCELLED
```

`ORDER_STATUS_TRANSITIONS` (`models.py`) is the literal source of truth
- `OrderManager` raises `InvalidOrderTransitionError` for anything not
in that table, rather than leaving the diagram above as a comment
nobody enforces:

| From | Allowed to |
|---|---|
| `NEW` | `VALIDATED`, `REJECTED` |
| `VALIDATED` | `SUBMITTED`, `REJECTED` |
| `SUBMITTED` | `FILLED`, `PARTIALLY_FILLED`, `CANCELLED`, `REJECTED` |
| `PARTIALLY_FILLED` | `FILLED`, `CANCELLED` |
| `FILLED` / `CANCELLED` / `REJECTED` | *(terminal - no further transitions)* |

`PaperBroker` (this phase's only `BrokerInterface`) always fills an
order completely and immediately at its own requested price - it never
produces `PARTIALLY_FILLED` itself. That state exists in the table
because a *live* broker adapter legitimately can partially fill an
order; `PaperBroker`'s simplicity is a property of this specific
broker, not a limitation of the order lifecycle it participates in.

## Position lifecycle

```
   OPEN ──────► PARTIALLY_EXITED ──────► CLOSED
    │                                       ▲
    └───────────────────────────────────────┘
              (a single full exit)
```

Every `Position` tracks average entry price (fixed at open - this
phase does not implement scaling into a position), quantity
(shrinking as exits happen), realized P&L (accumulated across every
exit, partial or full), and unrealized P&L (recomputed from whatever
price `update_unrealized_pnl()` was last given - it is a snapshot, not
a subscription to a live price feed, since this phase has no live feed
at all).

## Portfolio

`Portfolio` is always a fresh view, not independently-maintained state:
`total_equity = cash + sum(open positions' unrealized P&L)`, and
`drawdown = max(0, peak_equity - total_equity)` where `peak_equity` is
the highest total equity ever observed by `PortfolioManager.snapshot()`
- both computed at snapshot time, from `PositionManager`'s current
positions, never cached or duplicated.

## Broker abstraction

`BrokerInterface` (`Protocol`) defines exactly two operations -
`submit_order`/`cancel_order` - deliberately minimal, since everything
else (validation, state transitions, event publication) is
`OrderManager`'s job, not the broker's. `PaperBroker` is the only
implementation this phase provides: it simulates a fill immediately, in
full, at the order's own requested price - no partial fills, no
slippage, no candle-by-candle price checking. That realism (checking a
live/replayed price stream against stop-loss/target, the way
`app.trading.backtest.trade_executor` already does for historical
replay) is the Paper Trading Engine's job, not this architecture
phase's.

## Market session

`MarketCalendar` (`Protocol`) and `ConfigurableCalendar` (the one
reference implementation) support Pre-open/Open/Lunch/Close/After-hours/
Holiday phases from **constructor arguments only** - `SessionWindows`
has no default values for its required fields, and `holidays` is an
explicit `set[date]` the caller supplies. This is deliberately distinct
from (not a replacement for) `app.market_data.market_session` (frozen,
Phase 4), which only distinguishes PRE_MARKET/OPEN/CLOSED from a single
global `app.core.config.settings` window and has no lunch/holiday
concept at all - this package needed a richer model and built one
without touching the frozen one. A caller who wants NSE's actual
calendar constructs a `ConfigurableCalendar` with NSE's real hours and
holiday list; that data does not belong in this framework's code.

## Execution journal

`ExecutionJournal` is in-memory this phase (no database - the same
established pattern as `app.research.experiment_registry.
ExperimentRegistry`/`app.data.repository.HistoricalDataRepository`).
`subscribe_to(event_bus)` wires it onto every event type the CTO brief
names (Signals, Orders, Executions, Portfolio changes) automatically -
no manager needs to remember to also call into the journal. `
record_error()` is the one journal entry that isn't event-bus-driven,
since an error by definition means something didn't produce a normal
event.

## Performance monitor

`PerformanceMonitor` computes every metric purely by observing events -
it never calculates a P&L or a price itself. Execution latency is the
gap between an order's `OrderSubmittedEvent` and `OrderFilledEvent`
timestamps; win rate comes from closed positions' `realized_pnl` sign;
max drawdown reuses `Portfolio.drawdown` (computed once already by
`PortfolioManager`) rather than recomputing it from raw equity numbers.

## Replay philosophy

This phase's demo (`scripts/demo_paper_architecture.py`) drives the
existing pipeline against **one** hand-built candle snapshot - a single
decision, not a loop. The Paper Trading Engine (the next phase) is
where a continuous loop would exist: replaying historical candles
candle-by-candle (reusing `app.trading.backtest`'s existing replay
logic where it can, the same way this phase's demo reuses
`calculate_indicator_snapshot`/`build_market_context`/
`build_trading_conditions`/`run_strategies`/`build_risk_assessment`
directly rather than reimplementing any of them) or, later still,
driving off a live feed. Nothing in this phase assumes which of those
two the engine will choose first - the event-driven design here works
identically either way, since `MarketDataReceivedEvent` doesn't care
whether the candle behind it came from a CSV file or a live tick.

## Migration path to Live Broker

A live broker adapter (Zerodha or otherwise) is a second
`BrokerInterface` implementation, nothing more: it implements
`submit_order`/`cancel_order` against a real API instead of an
immediate simulated fill, and every other piece in this package -
`OrderManager`, `PositionManager`, `PortfolioManager`,
`ExecutionJournal`, `PerformanceMonitor`, every event type - is
unchanged, because none of them know or care which `BrokerInterface`
implementation they were given. The one thing a live adapter must
still respect that `PaperBroker` doesn't need to: real orders can
genuinely partially fill or reject asynchronously, so a live adapter's
integration will need to call back into `OrderManager` (or an
equivalent) to report those transitions as they arrive, rather than
returning a final `Order` synchronously the way `PaperBroker.
submit_order()` does today.

## Demo

`scripts/demo_paper_architecture.py` prints the full event sequence for
one decision - no real trade executed, no live connectivity used:

```bash
python3 scripts/demo_paper_architecture.py
```
