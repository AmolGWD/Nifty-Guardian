import type { DashboardSnapshot } from '../types'

/**
 * The one seam this dashboard depends on. A control button (see
 * components/Controls/) only ever calls one of these methods - it
 * never computes engine/session state itself. `MockDashboardService`
 * (mockDashboardService.ts) is the only implementation this phase
 * ships; a future `RestDashboardService`/`WebSocketDashboardService`
 * implements the exact same interface against the real
 * `app.runtime`/`app.paper_trading` backend, and no component or
 * store needs to change - see docs/DASHBOARD_GUIDE.md's "Backend
 * integration plan".
 */
export interface DashboardService {
  /** The current snapshot, synchronously - for initial render before any tick arrives. */
  getSnapshot(): DashboardSnapshot

  /** Called on every new snapshot. Returns an unsubscribe function. */
  subscribe(listener: (snapshot: DashboardSnapshot) => void): () => void

  start(): void
  pause(): void
  resume(): void
  stop(): void
  replay(): void
  reset(): void
}
