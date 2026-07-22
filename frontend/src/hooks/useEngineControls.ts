import { useDashboardStore } from './useDashboardStore'
import type { SessionState } from '../types'

export interface EngineControls {
  sessionState: SessionState
  start: () => void
  pause: () => void
  resume: () => void
  stop: () => void
  replay: () => void
  reset: () => void
}

/** The one hook Controls/ buttons use - every action is a direct service call, nothing computed. */
export function useEngineControls(): EngineControls {
  const sessionState = useDashboardStore((state) => state.snapshot.runtime.sessionState)
  const start = useDashboardStore((state) => state.start)
  const pause = useDashboardStore((state) => state.pause)
  const resume = useDashboardStore((state) => state.resume)
  const stop = useDashboardStore((state) => state.stop)
  const replay = useDashboardStore((state) => state.replay)
  const reset = useDashboardStore((state) => state.reset)

  return { sessionState, start, pause, resume, stop, replay, reset }
}
