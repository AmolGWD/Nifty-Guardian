import { create } from 'zustand'
import { dashboardService } from '../services'
import type { DashboardSnapshot } from '../types'

interface DashboardStoreState {
  snapshot: DashboardSnapshot
  start: () => void
  pause: () => void
  resume: () => void
  stop: () => void
  replay: () => void
  reset: () => void
}

/**
 * The single store every panel reads from. Every action is a direct,
 * unconditional call into `dashboardService` - the store computes
 * nothing and holds no engine/session logic of its own, mirroring the
 * CTO brief's "Buttons only call backend APIs. No business logic."
 * `dashboardService.subscribe()` is wired once, at module load, for
 * the lifetime of the app - swapping the mock service for a real
 * REST/WebSocket-backed one (see docs/DASHBOARD_GUIDE.md) does not
 * require touching this file, since both satisfy the same
 * `DashboardService` interface.
 */
export const useDashboardStore = create<DashboardStoreState>((set) => {
  dashboardService.subscribe((snapshot) => {
    set({ snapshot })
  })

  return {
    snapshot: dashboardService.getSnapshot(),
    start: () => dashboardService.start(),
    pause: () => dashboardService.pause(),
    resume: () => dashboardService.resume(),
    stop: () => dashboardService.stop(),
    replay: () => dashboardService.replay(),
    reset: () => dashboardService.reset(),
  }
})
