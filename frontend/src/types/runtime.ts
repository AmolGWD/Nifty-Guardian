/**
 * Mirrors app.runtime.session_controller.SessionState and
 * app.runtime.engine_config.ReplaySpeed (backend/app/runtime/) -
 * the operational state this console is a control surface for, not a
 * type this dashboard invents on its own.
 */
export type SessionState = 'NotStarted' | 'Running' | 'Paused' | 'Stopped' | 'Ended'

export type ReplaySpeed = '1x' | '2x' | '5x' | '10x' | 'Unlimited'

export interface RuntimeStats {
  sessionState: SessionState
  replaySpeed: ReplaySpeed
  processedCandles: number
  totalCandles: number
  eventsPublished: number
  ordersGenerated: number
  uptimeSeconds: number
}
