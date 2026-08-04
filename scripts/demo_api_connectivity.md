# Demo: Backend Connectivity (Phase 22)

Verifies the React Operations Dashboard connecting to the real
`app.runtime` backend over REST - no mock data, no WebSocket, no
broker integration. Every step below was actually run against this
repository during Phase 22 development, including the screenshots
referenced at the end.

## 1. Backend startup

```bash
cd backend
source .venv/bin/activate   # or: pip install -r requirements-dev.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verify it's up:

```bash
curl -sf http://localhost:8000/health
curl -sf http://localhost:8000/api/dashboard
```

The second call returns a complete, honest, empty snapshot before any
session has started:

```json
{
  "runtime": {
    "session_state": "NotStarted",
    "replay_speed": "1x",
    "processed_candles": 0,
    "total_candles": 0,
    "events_published": 0,
    "orders_generated": 0,
    "uptime_seconds": 0.0
  },
  "current_candle": null,
  "market_context": null,
  "orders": [],
  "positions": [],
  "portfolio": { "cash": 100000.0, "total_equity": 100000.0, "...": "..." }
}
```

## 2. Frontend startup (REST mode)

By default the dashboard runs against `MockDashboardService`
(`VITE_DASHBOARD_SERVICE=mock`, the setting from Phase 21). To connect
it to the real backend instead:

```bash
cd frontend
npm install
VITE_DASHBOARD_SERVICE=rest VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

(Equivalently, set `VITE_DASHBOARD_SERVICE=rest` in `frontend/.env` -
see `.env.example`.)

Open the printed local URL (typically `http://localhost:5173`).

## 3. Dashboard connecting successfully

On load, the dashboard immediately shows the real backend's
`NotStarted` state - Session badge `NOTSTARTED`, every panel in its
honest empty state (`"No market data yet - start the engine."`, `"No
orders yet."`, etc.), Portfolio already showing the real `100,000.00`
starting cash straight from the backend's `GET /api/dashboard`
response - confirming the REST connection is live, not showing stale
or fabricated data.

Zero browser console errors were observed throughout this entire demo
(verified via a headless Chromium session with `console --errors`
equivalent checks after every step).

## 4. Start / Pause / Resume against the real backend

Clicking **Start**:

- Frontend calls `POST /api/runtime/start`.
- Backend builds a fresh `RuntimeContext` (the same wiring
  `app.runtime.startup.start_runtime()` uses) against
  `backend/app/market_data/sample_data/nifty_sample_candles.csv` (75
  real candles) and begins replaying it on a background thread, 2
  seconds/candle (a demo-paced `candle_interval_seconds` - see
  `docs/API_GUIDE.md`).
  `Unlimited` replay speed is unaffected either way.
- Within a few polling ticks (1 second each, `VITE_DASHBOARD_POLLING_
  INTERVAL_MS`), the dashboard shows `Session: RUNNING`, `Processed
  Candles: N / 75` incrementing, and real journal entries appearing
  (newest first) as the backend's `ExecutionJournal` records each
  event.

Clicking **Pause**:

- Frontend calls `POST /api/runtime/pause`.
- Backend calls `SessionController.pause()` directly - the background
  thread notices at its next scheduler step and stops advancing.
- Dashboard shows `Session: PAUSED`, `Processed Candles` frozen at
  whatever count it reached, Pause/Start buttons now disabled, Resume/
  Stop enabled (mirroring the same `SESSION_STATE_TRANSITIONS`-based
  enablement rules as the mock).

Clicking **Resume**:

- Frontend calls `POST /api/runtime/resume`.
- Backend spawns a new background thread calling `engine.run()` again,
  which resumes automatically from `Paused` and continues from exactly
  the candle it left off at (the engine's candle iterator/history are
  held on `self`, per `docs/ENGINE_RUNTIME.md`'s documented resumable
  design).
- Dashboard shows `Session: RUNNING` again, `Processed Candles`
  continuing to climb from where it paused (not restarting from 0).

All three transitions were verified with real screenshots during
Phase 22 development - session state, processed-candle count, and
journal entries all changed exactly as described above, sourced
entirely from the real backend (confirmed by `Processed Candles: N /
75` - the real 75-candle sample dataset, distinct from the mock
service's 60-candle synthetic dataset).

## 5. Switching back to mock mode

No code change needed - set `VITE_DASHBOARD_SERVICE=mock` (or unset
it, since `mock` is the default) and reload. `services/index.ts` is
the only place that decides which `DashboardService` implementation
backs the dashboard; every component, hook, and the Zustand store
itself are unaware of which one is active.
