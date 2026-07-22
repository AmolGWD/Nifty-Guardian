# NIFTY Guardian — React Operations Dashboard Guide

This guide covers `frontend/src/` (the React Operations Dashboard,
Phase 21) - an operational control console for the Runtime Engine
(`app.runtime`, Phase 20), not a marketing page or a trading-logic
surface. Every value this dashboard displays comes from a backend
domain type; every control button calls a service method and computes
nothing itself. This phase ships entirely against a mock data service
- no REST call, no WebSocket, no live backend connectivity of any kind
(see "Backend integration plan" below for what that connection will
look like).

## Layout

Desktop-first, responsive, three-column trading-terminal layout - a
`Header` bar across the top, then three scrollable columns:

```
┌──────────────────────────────────────────────────────────────────┐
│ Header (title, session-state badge)                              │
├───────────────┬────────────────────────────┬─────────────────────┤
│ Left          │ Center                     │ Right               │
│               │                            │                     │
│ Engine        │ Chart Placeholder          │ Portfolio           │
│ Controls      │                            │ (Cash/Equity/       │
│               │ Trading                    │  Daily PnL/         │
│ Market        │ (Signal/Risk/              │  Drawdown)          │
│ (Candle +     │  Recommendation)           │                     │
│  Context)     │                            │ Runtime             │
│               │ Orders                     │ (Engine/Session     │
│ Health        │                            │  state, replay      │
│ (Latency/     │ Positions                  │  speed, counters)   │
│  Fill Ratio/  │                            │                     │
│  Engine       │                            │ Journal             │
│  Health)      │                            │ (scrollable log)    │
└───────────────┴────────────────────────────┴─────────────────────┘
```

Below 1200px the three columns collapse to a single scrolling column
(same panels, same order, top to bottom) rather than introducing a
second, separately-maintained mobile layout.

## Component hierarchy

```
app/App                                (theme.css, root shell)
└── pages/Dashboard/DashboardPage       (three-column composition, no logic)
    ├── components/Header
    ├── components/Controls/EngineControls
    ├── components/Market/MarketPanel
    ├── components/Health/HealthPanel
    ├── components/Market/ChartPlaceholder
    ├── components/Trading/TradingPanel
    ├── components/Orders/OrdersPanel
    ├── components/Positions/PositionsPanel
    ├── components/Portfolio/PortfolioPanel
    ├── components/Runtime/RuntimePanel
    └── components/Journal/JournalPanel
```

Every panel above is built from `components/Common/`'s shared
primitives - `Panel` (the bordered card + title every panel renders
inside), `StatRow` (label/value line), `Badge` (status pill), `DataTable`
(column-defined table, used by Orders/Positions), and `EmptyState`
(the "no data yet" placeholder every panel shows before the engine has
produced anything). No panel writes its own card chrome, table
markup, or empty-state text - a design change to any of those goes
through exactly one file.

Each panel reads its data through exactly one hook from `hooks/`
(`useRuntimeStats`, `useMarketData`, `useTradingSignal`, `useOrders`,
`usePositions`, `usePortfolio`, `useJournal`, `useHealth`,
`useEngineControls`) - a panel never reads the store directly, and
never computes a value the backend didn't already provide (a
"Confidence" field, for instance, is always
`StrategyEvaluation.strength`/`TradeRecommendation.
recommendationStrength` - the backend's own Strong/Moderate/Weak read,
never a number this dashboard invents).

## State management

Zustand, not Redux, not plain Context - a single store
(`hooks/useDashboardStore.ts`) holding one `DashboardSnapshot` plus six
action functions (`start`/`pause`/`resume`/`stop`/`replay`/`reset`).
Every action is an unconditional, one-line call into `services/
dashboardService.ts` - the store computes nothing and enforces no
transition rules of its own:

```ts
export const useDashboardStore = create<DashboardStoreState>((set) => {
  dashboardService.subscribe((snapshot) => set({ snapshot }))
  return {
    snapshot: dashboardService.getSnapshot(),
    start: () => dashboardService.start(),
    // ...
  }
})
```

`dashboardService.subscribe()` is wired once, at module load, for the
lifetime of the app. Selector hooks (`useRuntimeStats()`, `useOrders()`,
...) each read one slice of the snapshot via Zustand's selector
pattern, so a panel only re-renders when its own slice changes - a new
candle doesn't re-render the Journal panel, and a new journal entry
doesn't re-render the Portfolio panel.

`EngineControls`' enablement (which of Start/Pause/Resume/Stop/Replay/
Reset is clickable) mirrors the backend's own
`SESSION_STATE_TRANSITIONS` table (`app.runtime.session_controller`,
frozen) - this is a UI affordance (don't show a button the current
state can't act on), not a reimplementation of the state machine; the
service/backend remains the sole authority on whether a transition is
actually valid.

## Services

`services/dashboardService.ts` defines the one interface everything
above depends on:

```ts
export interface DashboardService {
  getSnapshot(): DashboardSnapshot
  subscribe(listener: (snapshot: DashboardSnapshot) => void): () => void
  start(): void
  pause(): void
  resume(): void
  stop(): void
  replay(): void
  reset(): void
}
```

`services/mockDashboardService.ts` is the only implementation this
phase ships. It replays `scripts/dashboard_mock_data.json` (60
synthetic 15-minute candles, generated with the same weekday-only/
warmup-aware conventions as the backend's own demo scripts) tick by
tick on a `setInterval`, exposing the same Start/Pause/Resume/Stop/
Replay/Reset semantics the real `SessionController` (Phase 20)
enforces:

- **start()** - `NotStarted` → `Running`, begins advancing ticks.
- **pause()/resume()** - halts/resumes the interval without losing
  progress.
- **stop()** - halts permanently until `replay()`.
- **replay()** - resets to tick 0 and the journal to empty, then runs
  again (mirrors the backend's `replay()`, which re-enters `Running`
  from `Stopped`/`Ended` without a fresh session).
- **reset()** - returns fully to `NotStarted` with an empty snapshot.

Orders/positions/portfolio/health/performance are full, cumulative
snapshots on every tick (matching how the real backend's managers
always hand back a fresh view, never a delta) - a journal entry is the
one append-only exception, since a journal is inherently a growing
log. The mock service's tick interval (`TICK_INTERVALS_MS`) is a UI
pacing choice, not the backend's literal `sleep_seconds_for()` - the
real `Unlimited` replay speed means zero delay (process as fast as
possible); a literal 0ms interval here would jump straight to the
final tick with nothing to watch, defeating the point of a "replay
progress" console.

`services/index.ts` exports the one `dashboardService` singleton every
hook imports. Swapping the mock for a real backend is a one-line
change to that file's assignment - see below.

## Backend integration plan

Nothing in `hooks/`, `components/`, or `pages/` talks to
`MockDashboardService` directly - every one of them depends on the
`DashboardService` interface. Connecting this dashboard to the real
`app.runtime`/`app.paper_trading` backend means:

1. Add a `RestDashboardService` (or `WebSocketDashboardService` - see
   below) implementing the same six methods plus `getSnapshot()`/
   `subscribe()`.
2. `start()`/`pause()`/`resume()`/`stop()`/`replay()`/`reset()` become
   HTTP calls (or emitted socket messages) to new FastAPI routes that
   wrap `app.runtime.session_controller.SessionController` and
   `app.runtime.runtime_engine.RuntimeEngine` - this dashboard's
   buttons already assume nothing beyond "calling this method changes
   backend state," so no button, hook, or panel needs to change.
3. `getSnapshot()` becomes an initial `GET` (or the first message on
   socket connect) that maps the backend's snake_case JSON
   (`Order`/`Position`/`Portfolio`/`HealthSnapshot`/...) into this
   dashboard's camelCase `types/` - deliberately kept as two separate
   shapes from day one (see `types/*.ts`'s own docstrings, each naming
   the exact backend model it mirrors) specifically so this mapping is
   the adapter's job, not a refactor of every component.
4. `subscribe()`'s callback becomes wherever new data arrives (a
   polling `GET` on an interval, or an incoming socket frame) instead
   of the mock's `setInterval` - the store doesn't know or care which.
5. Swap the single assignment in `services/index.ts`
   (`export const dashboardService: DashboardService = new
   MockDashboardService()`) for the real implementation. Every hook,
   every component, `useDashboardStore` itself - none of it changes.

## Future WebSocket migration

A polling `RestDashboardService` (steps above, against a `GET
/runtime/snapshot`-style endpoint) is the simplest first real backend,
but the `DashboardService` interface was designed for a socket from
the start: `subscribe(listener)` already models "push a new snapshot
whenever one exists," which is exactly a WebSocket message handler,
not a polling loop. A `WebSocketDashboardService` would:

- Open a connection to a new backend endpoint (e.g. `WS /runtime/live`)
  wrapping `app.paper_trading.event_bus.EventBus` - or, more likely,
  wrapping `app.runtime.health.HealthMonitor` and the managers
  directly, composing one `DashboardSnapshot`-shaped message per
  candle exactly the way `MockDashboardService.advanceTick()` does
  today, so the frontend's message shape doesn't change even though
  its source does.
- Call every `listener` in `subscribe()`'s set on each incoming
  message, precisely mirroring the mock's `emit()`.
- Send `start`/`pause`/`resume`/`stop`/`replay`/`reset` as outbound
  socket messages (or keep them as regular HTTP calls alongside a
  read-only socket stream - either is a legitimate choice the real
  backend implementation gets to make, since this dashboard's `
  DashboardService` interface doesn't constrain how actions get sent,
  only that they're one-line calls with no return value the UI
  depends on).

Nothing about `useDashboardStore`, any selector hook, or any panel
component needs to change for this migration - the same reason
`MarketDataSource`/`Scheduler` (`app.runtime`, Phase 20) are `Protocol`
seams the backend can swap without touching `RuntimeEngine`, this
frontend's `DashboardService` interface is that same seam one layer up
the stack.

## Demo

`scripts/dashboard_mock_data.json` is the realistic mock dataset this
whole dashboard runs from - 60 synthetic candles, an EMA-breakout-style
uptrend, two trades (one closed profitably, one left open at the final
tick so the Positions panel has something to show). Run the dashboard
itself with:

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL, click **Start**, and watch the console
populate - candle data, signals, orders, positions, portfolio, and
journal entries - entirely from the mock service, no backend required.
