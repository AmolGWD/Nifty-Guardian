# NIFTY Guardian — Signal Engine, Telegram Alerts & Dummy Trade Tracking

This guide covers `backend/app/signals/`, `backend/app/notifications/`,
and `backend/app/api/signals/` - the operational signal engine turning
the already-completed, already-approved trading platform into a
"leave it running, get alerted" tool. **No automated order placement,
no real broker execution, no new trading logic anywhere in this
phase** - every signal was already decided by the frozen Strategy/
Risk/Decision Engines and paper-executed by the frozen `PaperBroker`
before this layer ever sees it.

## Architecture

```
Live Market Data (app.live.ReplayMarketFeed, or a real feed - unchanged)
        │
        ▼
RuntimeEngine + EventProcessor (frozen, app.runtime)
  Indicators → MarketContext → TradingConditions → Strategy Engine →
  Risk Engine → Decision Engine → OrderManager → PaperBroker
        │
        │ publishes on the frozen EventBus: SignalGeneratedEvent,
        │ OrderFilledEvent, PositionUpdatedEvent, MarketDataReceivedEvent
        ▼
SignalService (new, this phase - a pure subscriber, zero changes to any frozen file)
  1. cache StrategyEvaluation per strategy (reasons/strength)
  2. on OrderFilledEvent: compute Guardian Score, run SignalFilter
  3. if allowed: open a DummyTrade, update dashboard state, send a Telegram alert
  4. on PositionUpdatedEvent (Closed): close the DummyTrade, infer exit reason, alert
  5. on market close: build + export + Telegram the daily report
        │                                   │
        ▼                                   ▼
NotificationService                  DummyTradeTracker
  (app.notifications)                  (app.signals)
  Telegram, or a no-op                  in-memory trade history
  log line if disabled
        │
        ▼
app.api.signals (REST) - new, parallel to app.api.dashboard (untouched)
  GET  /api/signals/{state,performance,trades,report/today}
  POST /api/signals/{start,stop,report/export}
        │
        ▼
React Dashboard - Signals column (new, 4th column)
  Signal State, Dummy Trades, Performance panels -
  the original three columns are completely untouched
```

### Files

| File | Responsibility |
|---|---|
| `app/signals/models.py` | `GuardianScore`, `SignalType`, `ExitReason`, `DummyTrade`, `DailyPerformanceReport`, `SignalConfig` (env-driven) |
| `app/signals/confidence_engine.py` | `compute_guardian_score()` - the new, numeric 0-100 aggregate |
| `app/signals/signal_filter.py` | Dedup, cooldown, max-signals/day, trading-hours enforcement |
| `app/signals/dummy_trade_tracker.py` | Opens/closes `DummyTrade`s, infers exit reason, builds daily reports |
| `app/signals/report_exporter.py` | Writes a `DailyPerformanceReport` to `backend/data/reports/<date>.json` |
| `app/signals/signal_service.py` | The orchestrator - subscribes to the frozen `EventBus`, ties everything together |
| `app/signals/signal_runtime.py` | `start_signal_engine()` - wires `app.live.start_live_runtime()` + `SignalService` |
| `app/notifications/` | `NotificationConfig`, `NotificationService`, `HttpTelegramClient`, message formatting |
| `app/api/signals/` | REST layer - a new session service + router, parallel to `app.api.dashboard` |

## Two reuse decisions worth explaining

**`SignalService` never recomputes anything the frozen platform already
computed.** It only subscribes to events the frozen `EventBus` already
publishes (`SignalGeneratedEvent` for reasons/strength,
`OrderFilledEvent` for the concrete entry price/stop-loss/target,
`PositionUpdatedEvent` for the close). No `IndicatorSnapshot` is
recomputed, no strategy is re-run, no risk decision is re-made - this
is purely a reporting layer bolted onto the existing, approved
decision chain.

**The Signal Engine reuses `app.live.start_live_runtime()`, not
`app.runtime.startup.start_runtime()` directly.** `LiveRuntimeContext`
already exposes a public `event_bus` field (Phase 24) - `SignalService.
subscribe_to(event_bus)` attaches to it after construction, exactly
the way `ExecutionJournal`/`PerformanceMonitor` already attach inside
`start_runtime()` itself. Zero changes to any frozen file were needed.
The broker passed in is always `PaperBroker` - this package creates
dummy trades only.

## Guardian Score

A single, explainable 0-100 number, computed in `confidence_engine.py`:

```
base(strength)  = Strong: 70, Moderate: 55, Weak: 35
rr_bonus         = min(reward_risk_ratio / 3.0, 1.0) * 30
score            = min(base + rr_bonus, 100.0)
```

`strength` is `StrategyEvaluation.strength` (frozen, unchanged) -
reported side by side as "Confidence," never replaced. The Guardian
Score is this phase's own addition, blending that categorical read
with the reward:risk ratio implied by the filled order's own
stop-loss/target.

## Signal filtering

`SignalFilter.should_emit()` checks, in order:

1. **Trading hours** - `settings.market_open`/`market_close` (default
   09:15-15:30), compared via the same naive `strftime("%H:%M")`
   technique `app.runtime.event_processor` itself uses - deliberately
   *not* `app.market_data.market_session.market_session_service`,
   which converts to IST via `.astimezone()` and would silently shift
   the comparison whenever the process's system timezone isn't IST.
2. **Confidence threshold** - `SIGNAL_CONFIDENCE_THRESHOLD` (default 65.0).
3. **Cooldown** - `SIGNAL_COOLDOWN_MINUTES` (default 15), tracked per strategy.
4. **Max signals/day** - `SIGNAL_MAX_SIGNALS_PER_DAY` (default 5).

A rejection for low confidence specifically also triggers a "NO
TRADE" Telegram notification (itself cooldown-limited, so it can't
spam every rejected candle either).

## Dummy trading

Every accepted signal opens a `DummyTrade` from the already-filled
`Order`'s own entry/stop-loss/target. Correlating the trade's close
back to the frozen `Position` lifecycle relies on `app.paper_trading`'s
own documented invariant that at most one position is open at a time
- see `signal_service.py`'s module docstring for the exact mechanism.
`Position` never records an exit price directly (only realized P&L) -
`_infer_exit_price()` derives it from the same `_signed_pnl()` formula
`PositionManager` itself uses; `exit_reason` (Target/StopLoss/EndOfDay)
is inferred by comparing that derived exit price to the trade's own
stored target/stop-loss, with a small tolerance.

## Telegram setup

```bash
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=<your bot token>
TELEGRAM_CHAT_ID=<your chat id>
```

`TELEGRAM_ENABLED=false` (the default) means every notification is
logged only - no network access of any kind. `HttpTelegramClient` uses
only the Python standard library (`urllib.request`) - no new runtime
dependency for a single HTTP POST. Message types: BUY CE, BUY PE,
TARGET HIT, STOPLOSS HIT, NO TRADE, Daily Summary, Critical Errors,
Runtime Started/Stopped - see `app/notifications/message_formatter.py`
for the exact format.

## End-of-day report

Auto-generated once the market transitions from Open to Closed for a
given date (never on a pre-market-only candle - see
`SignalService._on_market_data()`), sent via Telegram, and exported to
`backend/data/reports/<report_date>.json`. `POST /api/signals/report/export`
also triggers an on-demand export of the trade history so far, useful
mid-session or for a demo.

## REST API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/signals/start` | Start a Signal Engine session (the sample dataset, replayed) |
| `POST` | `/api/signals/stop` | Stop it |
| `GET` | `/api/signals/status` | Is a session running |
| `GET` | `/api/signals/state` | Current market bias, latest signal, Guardian Score, reasons |
| `GET` | `/api/signals/performance` | Open/closed trades, win rate, today/weekly/monthly PnL |
| `GET` | `/api/signals/trades` | Full dummy trade history |
| `GET` | `/api/signals/report/today` | Today's end-of-day report |
| `POST` | `/api/signals/report/export` | Export today's report to JSON now |

## Honest limitations

- **Only "BUY CE"-style (LONG) signals can actually fire.** The frozen
  `app.runtime.event_processor._evaluate_entry()` requires
  `recommendation.direction == StrategyDirection.LONG` before
  submitting an order - a deliberate simplification from an earlier,
  already-approved phase, not something this phase can or should
  change. Every `BUY PE`/`SignalType.BUY_PE` type is fully implemented
  and will work the day a future, explicitly-authorized phase adds
  SHORT order submission to the runtime.
- **OI and Pivot are named in the Telegram message template but not
  evaluated by the currently-registered strategy.** `GuardianScore.reasons`
  reuses exactly what `EMABreakoutStrategy` (frozen) already produces -
  EMA/RSI/VWAP/SuperTrend/Trend agreement. No fabricated reason lines
  are ever printed for checks the strategy doesn't actually perform.
- **Exit reason is inferred, not authoritative.** `Position` (frozen)
  never records why it closed - only the realized P&L. The inference
  in `dummy_trade_tracker.py` is a best-effort classification against
  the trade's own stored target/stop-loss, not a value the backend
  ever explicitly decided.
