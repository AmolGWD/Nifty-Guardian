# NIFTY Guardian — Backend Connectivity (API) Guide

This guide covers `backend/app/api/dashboard/` (Phase 22) - the REST
layer connecting the React Operations Dashboard (Phase 21) to the real
Runtime Engine (`app.runtime`, Phase 20), and
`frontend/src/services/api/` + `RestDashboardService` - the frontend
half of that connection. Replaces `MockDashboardService` as the
dashboard's data source; the dashboard UI itself (components, layout,
Zustand store, selector hooks - all frozen this phase) is unchanged.
No WebSocket, no live broker integration - both remain later,
not-yet-authorized phases.

## REST endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/dashboard` | Complete dashboard snapshot |
| `GET` | `/api/runtime/health` | Runtime health (`HealthSnapshot`) |
| `GET` | `/api/runtime/state` | Current session state only |
| `POST` | `/api/runtime/start` | Start a fresh session |
| `POST` | `/api/runtime/pause` | Pause the running session |
| `POST` | `/api/runtime/resume` | Resume a paused session |
| `POST` | `/api/runtime/stop` | Stop the session |
| `POST` | `/api/runtime/replay` | Discard the current session, start a new one |

Every action endpoint (`start`/`pause`/`resume`/`stop`/`replay`)
returns the same `RuntimeStatsResponse` shape a `GET /api/dashboard`
call's `runtime` field would show - so a caller never has to make a
second request to see the result of an action it just took.

## Request models

`POST /api/runtime/replay` is the only endpoint with a body
(`ReplayRequest`, `backend/app/api/dashboard/runtime_models.py`):

```json
{
  "replay_speed": "1x",
  "maximum_candles": 30
}
```

Both fields are optional - omitted, `replay_speed` defaults to `"1x"`
and `maximum_candles` to `null` (the entire sample dataset, 75
candles). `replay_speed` is one of `1x`/`2x`/`5x`/`10x`/`Unlimited`
(`app.runtime.engine_config.ReplaySpeed`, frozen) - an invalid value
is rejected by FastAPI's own Pydantic validation (422) before it ever
reaches the runtime.

Every other endpoint takes no body.

## Response models

`backend/app/api/dashboard/dashboard_models.py` defines exactly two
new types - `RuntimeStatsResponse` and `DashboardSnapshotResponse` -
and reuses every other field's type directly from the frozen domain
models that already own it (`Candle`, `MarketContext`,
`StrategyEvaluation`, `RiskAssessment`, `TradeRecommendation`, `Order`,
`Position`, `JournalEntry`, `HealthSnapshot`, `PerformanceSnapshot`).
Every field name is `snake_case` (Pydantic's default), matching the
backend's own convention everywhere else in this codebase -
`frontend/src/services/wireMapping.ts` is the one place that maps
these into the dashboard's camelCase domain types.

```
GET /api/dashboard  ->  DashboardSnapshotResponse
{
  "runtime": RuntimeStatsResponse,
  "current_candle": Candle | null,
  "market_context": MarketContext | null,
  "latest_signal": StrategyEvaluation | null,
  "latest_risk_decision": RiskAssessment | null,
  "latest_recommendation": TradeRecommendation | null,  // always null - see below
  "orders": Order[],
  "positions": Position[],
  "portfolio": Portfolio,
  "journal": JournalEntry[],
  "health": HealthSnapshot,
  "performance": PerformanceSnapshot
}
```

### Two honest, documented gaps

**`latest_recommendation` is always `null` this phase.** No event on
`app.paper_trading.event_bus.EventBus` (frozen) carries a
`TradeRecommendation` - `EventProcessor._evaluate_entry()` (frozen,
`app.runtime`) computes one internally via `build_trade_recommendation()`
but only acts on it, never publishes it. Recomputing it independently
in this API layer would mean re-running the Strategy/Risk/Decision
pipeline a second time outside the package that owns it - exactly the
"new trading logic" this whole engagement has avoided - so this is
left honestly `null` rather than duplicated. The frozen `TradingPanel`
already renders a graceful "No recommendation yet" for a `null` value,
so this degrades safely rather than breaking anything.

**`latest_risk_decision` only ever reflects an *approved* assessment.**
`RiskApprovedEvent` (frozen) is published only when `risk_ok` is
`true` - a risk-rejected evaluation leaves this field showing whatever
the last *approved* assessment was, not "rejected." This is a faithful
mirror of what the frozen event surface actually publishes, not a bug.

### One real defect found and fixed (in new code only)

`app.paper_trading.models.Portfolio` (frozen, Phase 19) defines
`drawdown`/`drawdown_percent` as plain `@property`, not
`@computed_field`. Pydantic v2 (and therefore FastAPI's JSON response
serialization) silently omits plain `@property` from
`model_dump()`/JSON output - so these two fields were invisible to any
REST consumer, including this very API, despite the frozen
`PortfolioPanel` (Phase 21) already rendering both. No endpoint
existed before this phase to expose `Portfolio` over JSON at all, so
this was a real, previously-latent gap.

Fixed entirely within this phase's own, unfrozen code -
`PortfolioResponse` (`dashboard_models.py`) subclasses the frozen
`Portfolio` and re-declares both properties as `@computed_field
@property`, reusing the parent's exact formula via `super().drawdown`/
`super().drawdown_percent` rather than duplicating it. `app.paper_trading.
models` itself is untouched.

## Polling strategy

No WebSocket this phase - the frontend polls `GET /api/dashboard` on
an interval (`VITE_DASHBOARD_POLLING_INTERVAL_MS`, default `1000`ms).
`RestDashboardService` (`frontend/src/services/restDashboardService.ts`):

1. Fetches immediately on construction (so the dashboard shows real
   data as soon as possible, not just after the first interval tick).
2. Re-fetches every `pollingIntervalMs`.
3. After any action (`start`/`pause`/`resume`/`stop`/`replay`)
   succeeds *or fails*, immediately triggers one extra fetch outside
   the regular interval - so clicking a button reflects its result
   without waiting up to a full polling interval.

### Error handling

Three distinct failure modes, matching the CTO brief's "Loading /
Network error / Backend unavailable / Timeout / Graceful retry":

- **Loading** - before the first successful fetch resolves,
  `getSnapshot()` returns an honest, empty `NotStarted`-shaped snapshot
  (the same philosophy `MockDashboardService` already uses before
  `start()` is called) - the frozen components already render their
  own `EmptyState` for this shape, so no new UI is needed.
- **Timeout** - `apiRequest()` (`services/api/client.ts`) aborts any
  request exceeding `VITE_API_TIMEOUT_MS` (default `5000`ms) via
  `AbortController`, throwing `ApiTimeoutError`.
- **Network error / backend unavailable** - a `fetch()` that never
  reaches a server (connection refused, DNS failure, CORS rejection)
  throws `ApiNetworkError`.
- **Backend responded with an error** - any non-2xx HTTP status throws
  `ApiHttpError`, carrying the status code and the backend's own
  `detail` message (e.g. a 409 from an invalid runtime transition).
- **Graceful retry** - `RestDashboardService` catches all three error
  types at both the polling loop and the action layer, logs a
  descriptive `console.warn`, and does nothing else: it does not clear
  the snapshot, does not stop polling, does not throw into the (frozen)
  Zustand store. The next interval tick simply tries again. Recovery
  is automatic and silent from the UI's perspective - the CTO brief's
  "No component changes" meant there is no new connection-status
  indicator this phase, so resilience lives entirely in the service
  layer instead.

`reset()` is the one `DashboardService` method with no backend
equivalent - the brief's endpoint list has no `POST /api/runtime/reset`.
Rather than silently mapping it to `stop()` or `replay()` (each of
which means something different), `RestDashboardService.reset()` logs
a clear "known gap, not a failure" warning and does nothing. A future
phase that wants Reset to mean something specific over REST should add
the endpoint explicitly rather than have this guessed at.

## Configuration

Every new environment variable (`frontend/.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend origin (already existed) |
| `VITE_DASHBOARD_SERVICE` | `mock` | `mock` or `rest` - which `DashboardService` backs the dashboard |
| `VITE_DASHBOARD_POLLING_INTERVAL_MS` | `1000` | Polling interval |
| `VITE_API_TIMEOUT_MS` | `5000` | Per-request timeout before `ApiTimeoutError` |
| `VITE_DEFAULT_REPLAY_SPEED` | `1x` | Sent with `POST /api/runtime/replay` when the UI doesn't specify one |

`services/config.ts`'s `loadDashboardConfig()` reads all of these with
explicit, honest defaults - a missing or malformed value never crashes
the dashboard, it just falls back rather than fails to render.

## Runtime hosting: background thread, demo-paced replay

`DashboardRuntimeService` (`backend/app/api/dashboard/dashboard_service.py`)
wires the exact same components `app.runtime.startup.start_runtime()`
wires, in the same order (see `docs/ENGINE_RUNTIME.md`'s "Startup
sequence"), plus one addition of its own: an `_EventObserver`
subscribed to the event bus, since `GET /api/dashboard` needs "what
was the most recent candle/signal/risk decision" and neither
`EventProcessor` nor any manager exposes that as public state - only
as transient events (the same "learn everything from observation"
discipline `ExecutionJournal`/`PerformanceMonitor`/`HealthMonitor`
already use).

Two deliberate, documented API-layer choices, neither a change to
`app.runtime`:

- **`RuntimeEngine.run()` runs on a background OS thread**, since it
  blocks its calling thread inside a synchronous scheduler loop -
  `docs/ENGINE_RUNTIME.md` already documents this as the exact seam an
  async (or, here, threaded) host is expected to use.
- **`candle_interval_seconds` is set to 2 seconds**, not the real
  15-minute (900s) default - `start_runtime()` doesn't expose this
  constructor argument, so `DashboardRuntimeService` wires
  `RuntimeEngine` directly instead (still every other frozen
  component, same order). The real 900s default is correct for
  realistic pacing but far too slow for a human polling this REST API
  to watch progress in any reasonable demo session; `Unlimited` replay
  speed is unaffected either way (`sleep_seconds_for()` always returns
  `0.0` for `Unlimited`, regardless of interval).

Market data comes from the existing `scripts/sample_data/
nifty_sample_candles.csv` (75 candles) via `HistoricalReplaySource`
(frozen, unchanged) - no new sample data was generated for this phase.

## Migration to WebSocket

Nothing about `RestDashboardService`'s callers changes if it's ever
replaced by a `WebSocketDashboardService` - both satisfy the same
`DashboardService` interface (`services/dashboardService.ts`, frozen
this phase), and `services/index.ts`'s single assignment is the only
line that would change.

A future `WebSocketDashboardService` would:

- Open a connection to a new backend endpoint (e.g. `WS /runtime/live`)
  that pushes one `DashboardSnapshotResponse`-shaped message per
  candle - composing it exactly the way `DashboardRuntimeService.
  dashboard_snapshot()` does today, so the message shape doesn't
  change even though its delivery mechanism does.
- Call every `subscribe()` listener on each incoming message, exactly
  mirroring `RestDashboardService.refresh()`'s `emit()` call - the
  polling `setInterval` is replaced by the socket's own message
  handler, nothing else in the class changes shape.
- Likely keep `start`/`pause`/`resume`/`stop`/`replay` as regular HTTP
  POSTs alongside a read-only socket stream, or send them as outbound
  socket messages - either is legitimate, since `DashboardService`'s
  interface doesn't constrain how actions are sent, only that they're
  fire-and-forget calls with no return value the UI depends on.
- Still need the same graceful-degradation story this phase already
  built: a dropped connection should keep the last known-good snapshot
  visible and retry (reconnect) rather than clear the dashboard -
  `RestDashboardService`'s "never throw into the store, never clear on
  failure" discipline carries over unchanged.

## Demo

See `scripts/demo_api_connectivity.md` for backend/frontend startup,
verifying the dashboard connects, and exercising Start/Pause/Resume
against the real backend end to end.
