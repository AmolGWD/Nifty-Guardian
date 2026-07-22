# NIFTY Guardian — Live Trading Mode Guide

This guide covers `backend/app/live/` (Phase 24) - the orchestration
layer that wires the frozen Runtime Engine (`app.runtime`), a Live
Market Feed abstraction (this phase), and a broker adapter
(`app.brokers.ZerodhaBroker`, or `PaperBroker` for a dry run, both
frozen) together behind a safety/heartbeat/reconnect layer. It
introduces **no new strategy logic** - every candle is still processed
by the exact same frozen `EventProcessor` every other phase already
uses. This phase does **not** implement WebSocket streaming, does
**not** deploy anything to production, and never places a real order -
`ReplayMarketFeed` (replay data) and a mocked broker are the only
concrete implementations exercised by this phase's tests and demo.

## Architecture

```
                         ┌───────────────────────┐
                         │      LiveSession        │  (this phase - state machine)
                         │  Initializing → Connecting →│
                         │  Connected → Trading ⇄ Paused│
                         │  → Stopping → Stopped         │
                         │  (+ Disconnected, Error)       │
                         └──────────┬────────────┘
                                    │ delegates to
        ┌───────────────┬──────────┼──────────────┬────────────────┐
        │               │          │              │                │
  ┌─────┴─────┐  ┌──────┴─────┐ ┌──┴────────┐ ┌───┴────────┐ ┌─────┴──────┐
  │ SafetyManager│ │HeartbeatMon│ │ReconnectMgr│ │LiveMarketFeed│ │RuntimeEngine│
  │ (this phase) │ │(this phase)│ │(this phase)│ │Interface     │ │(frozen)     │
  └──────────────┘ └────────────┘ └────────────┘ └──────┬───────┘ └──────┬──────┘
                                                          │                │
                                                  ReplayMarketFeed   MarketDataSource
                                                  (this phase's           │ Protocol
                                                   only feed)             │ (frozen)
                                                          │                │
                                                          └──► LiveFeedMarketDataSource ──┘
                                                               (this phase's bridge adapter)

  ┌────────────────┐        BrokerInterface Protocol (frozen)
  │  OrderExecutor   │◄──────────────────────────────────────────┐
  │  (this phase -   │                                            │
  │   decorator, itself│                                          │
  │   implements       │                       ┌──────────────────┴──┐
  │   BrokerInterface)  │──submit/cancel──────►│ PaperBroker / ZerodhaBroker│  (frozen)
  └─────────┬───────────┘                       └──────────────────────┘
            │ passed to EventProcessor as *its* broker
            ▼
  ┌───────────────────┐
  │   EventProcessor     │  (frozen, app.runtime)
  │   OrderManager        │  (frozen, app.paper_trading - already
  │   publishes            │   publishes OrderSubmittedEvent/
  │   OrderFilledEvent etc │   OrderFilledEvent/etc for whatever
  └────────────────────────┘   BrokerInterface it's given)
```

### Files

| File | Responsibility |
|---|---|
| `models.py` | `LiveSessionState` + `LIVE_SESSION_STATE_TRANSITIONS`, `LiveConfig` (env-driven), `SafetyDecision`/`HeartbeatSnapshot`/`ReconnectOutcome` |
| `live_market_feed.py` | `LiveMarketFeedInterface` Protocol, `ReplayMarketFeed` (this phase's only feed), `LiveFeedMarketDataSource` (bridge into the frozen `MarketDataSource` Protocol) |
| `order_executor.py` | `OrderExecutor` - retries transient broker failures, tracks last-known order status, itself satisfies `BrokerInterface` |
| `safety_manager.py` | `SafetyManager` - kill switch, emergency stop, circuit breaker, trading hours, daily order/loss/position caps |
| `heartbeat.py` | `HeartbeatMonitor` - tracks last-seen timestamps for broker/market_feed/runtime/dashboard, reports staleness |
| `reconnect.py` | `ReconnectPolicy` (exponential backoff), `ReconnectManager` (bounded retries, no order replay) |
| `live_session.py` | `LiveSession` - the state machine tying every component together |
| `live_runtime.py` | `start_live_runtime()` - wires everything, mirrors `app.runtime.startup.start_runtime()`'s own wiring order |

## Two seam-reuse patterns worth calling out

**The bridge adapter.** `LiveMarketFeedInterface` is push-based
(`subscribe(callback)`); the frozen `MarketDataSource` Protocol
`RuntimeEngine` requires is pull-based (`__iter__`/`__len__`).
`LiveFeedMarketDataSource` bridges the two via a thread-safe
`queue.Queue`: it subscribes its own `queue.put` to the feed at
construction time, and `__iter__` blocks (bounded by a timeout) for
each next candle. This is exactly what `docs/ENGINE_RUNTIME.md`
already predicted - "a future live source would be a third
implementation of the same Protocol" - and it means `RuntimeEngine`
itself needed zero changes.

**The decorator satisfying the same Protocol.** `OrderExecutor` wraps
any concrete broker (`PaperBroker` or `ZerodhaBroker`) and itself
implements `BrokerInterface` - so it can be handed to `EventProcessor`
as *its* broker. Since `OrderManager` (frozen) already publishes
`OrderSubmittedEvent`/`OrderFilledEvent`/etc for whatever
`BrokerInterface`-compatible object it's given, "translate broker
events into runtime events" is already satisfied by the existing
frozen machinery once `OrderExecutor` sits at the broker seam - no new
event-publishing code was needed.

## Safety philosophy

`SafetyManager` never decides *what* to trade - only whether the
system is currently *permitted* to act at all, the same "permission,
not decision" discipline `app.trading.conditions` (frozen) already
established at the market layer. Every gate answers a single yes/no
question, checked in a fixed order so the first failing gate always
wins and is always the one reported:

1. **Emergency stop** - an absolute, always-checked-first override.
2. **Kill switch** - a manual halt, engaged/disengaged independently of the emergency stop.
3. **Circuit breaker** - trips after `circuit_breaker_threshold` consecutive order failures; resets on the next success.
4. **Trading hours** - `TRADING_START`/`TRADING_END`, inclusive.
5. **Max orders per day** - `MAX_ORDERS_PER_DAY`.
6. **Max daily loss** - `MAX_DAILY_LOSS`; only realized *losses* count against the cap, gains never do.
7. **Max open positions** - `MAX_OPEN_POSITIONS`.

If every gate passes, `check_before_order()` returns an `allowed=True`
decision with `gate="all_gates"`. Every decision - allowed or rejected
- is appended to `SafetyManager.decisions` and logged via the standard
`logging` module, so a rejection is always auditable after the fact,
never a silent `False`.

### Kill switch

`engage_kill_switch(reason)` / `disengage_kill_switch()` - a manual,
reversible halt an operator can flip independently of any automatic
condition. Unlike emergency stop, it's meant to be turned back off
once whatever prompted it is resolved.

### Emergency stop

`trigger_emergency_stop(reason)` - a one-way, safety-critical action.
`LiveSession.emergency_stop()` is reachable from any non-terminal
session state, always disconnects the market feed, and always drives
the session to `Stopped`. There is no "un-emergency-stop" - starting
again means building a new session.

## Heartbeat

`HeartbeatMonitor` tracks a last-seen timestamp per component
(`broker`, `market_feed`, `runtime`, `dashboard`) and reports staleness
purely by observing elapsed time - the same "learn everything from
observation, compute nothing new" discipline
`app.runtime.health.HealthMonitor` (frozen) already established. A
component with no recorded heartbeat is always stale; once
`HEARTBEAT_INTERVAL` seconds elapse since the last recorded heartbeat,
it goes stale until the next `record()` call.

## Reconnect

`ReconnectPolicy.next_delay(attempt)` computes exponential backoff:
`min(base_delay_seconds * 2^attempt, max_delay_seconds)`.
`ReconnectManager.reconnect(attempt_connect)` calls the given
connect-attempt callable up to `RECONNECT_LIMIT` times, sleeping the
computed delay before each attempt, and returns a `ReconnectOutcome`
recording whether it ultimately succeeded, how many attempts it took,
and the total delay spent.

**Deliberately, no automatic order replay.** Reconnecting restores
connectivity only - it never resubmits whatever order might have been
in flight when the connection dropped. Silently replaying an order
after a disconnect risks placing a duplicate the operator never asked
for twice; the safer default is to surface the gap (via
`OrderExecutor.last_known_status()`) and let a human decide, not guess.

## Recovery

`LiveSession.attempt_reconnect()` transitions to `Connecting`, drives
the market feed's `connect()`/`is_connected()` through
`ReconnectManager`, and on success re-records heartbeats and
transitions to `Connected` - the session can then resume trading
exactly as it would after a fresh `connect()`. On exhaustion, the
session transitions through `Stopping` to `Stopped` rather than
retrying forever or guessing at a recovery it can't confirm.

## Failure scenarios

| Scenario | What happens |
|---|---|
| Market feed fails to connect | `LiveSession.connect()` catches the exception, transitions to `Error` |
| Connection drops mid-session | Caller invokes `mark_disconnected()` → `Disconnected`; `attempt_reconnect()` drives recovery |
| Reconnect exhausts `RECONNECT_LIMIT` | Session transitions `Disconnected`/`Error` → `Stopping` → `Stopped` |
| Broker raises a transient error (`ConnectionError`, `RateLimitError`, `BrokerUnavailableError`) | `OrderExecutor` retries up to `max_retries` times with a delay between attempts |
| Broker raises a permanent error (`OrderRejectedError`, `AuthenticationError`, `MappingError`) | `OrderExecutor` raises immediately - retrying a rejected/rejected-forever request only repeats the same mistake |
| Consecutive order failures reach the circuit-breaker threshold | `SafetyManager.check_before_order()` rejects with `gate="circuit_breaker"` until a success resets the counter |
| Operator needs to halt trading immediately | `LiveSession.emergency_stop(reason)` - reachable from any non-terminal state, always stops the session |

## Configuration

All environment-driven, loaded once via `LiveConfig` (never hardcoded),
safe defaults throughout:

| Variable | Default | Meaning |
|---|---|---|
| `LIVE_MODE` | `false` | Master switch - `false` means "do not trade live" |
| `MAX_DAILY_LOSS` | `10000.0` | Realized-loss cap per day |
| `MAX_OPEN_POSITIONS` | `1` | Concurrent open positions cap |
| `MAX_ORDERS_PER_DAY` | `10` | Order-count cap per day |
| `HEARTBEAT_INTERVAL` | `5.0` | Seconds before a component is considered stale |
| `RECONNECT_LIMIT` | `5` | Maximum reconnect attempts before giving up |
| `TRADING_START` | `09:15` | Trading-hours gate start (`HH:MM`) |
| `TRADING_END` | `15:30` | Trading-hours gate end (`HH:MM`) |

## Operational checklist

Before enabling `LIVE_MODE`, confirm:

- [ ] `MAX_DAILY_LOSS`, `MAX_OPEN_POSITIONS`, `MAX_ORDERS_PER_DAY` are set to values you've actually reviewed, not left at defaults.
- [ ] `TRADING_START`/`TRADING_END` match the session hours you intend to trade.
- [ ] `RECONNECT_LIMIT` and `HEARTBEAT_INTERVAL` are tuned for how quickly you want a stalled connection to surface.
- [ ] A kill switch is reachable and its `engage_kill_switch()`/`disengage_kill_switch()` path has been exercised at least once outside of a test.
- [ ] `SafetyManager.decisions` (or the underlying log stream) is actually being monitored somewhere a human will see it.
- [ ] The broker passed to `start_live_runtime()` is the one you intend - `PaperBroker` for a dry run, `ZerodhaBroker` only once credentials and mapping have been verified (see `docs/ZERODHA_ADAPTER_GUIDE.md`).
- [ ] The market feed passed in is understood: this phase ships only `ReplayMarketFeed` (known, finite candle lists) - a real-time feed is out of scope until WebSocket streaming is built.
- [ ] `OrderExecutor.last_known_status()` is checked after any reconnect, since reconnect never replays orders automatically.

## What this phase does not do

- No WebSocket streaming - `LiveMarketFeedInterface` is an abstraction only; `ReplayMarketFeed` is its only implementation.
- No production deployment - no containers, no process supervisors, no infrastructure.
- No real order placement - every test and the demo script use fakes/mocks exclusively.
- No new strategy logic - `EventProcessor`, `StrategyRegistry`, and every strategy are reused unmodified.
