import type { SessionState } from './runtime'

/** Mirrors app.runtime.health.HealthSnapshot (backend, frozen). */
export interface HealthSnapshot {
  processedCandles: number
  averageProcessingLatencySeconds: number | null
  uptimeSeconds: number
  eventsPublished: number
  ordersGenerated: number
  currentState: SessionState
}

/** Mirrors app.paper_trading.performance_monitor.PerformanceSnapshot (backend, frozen). */
export interface PerformanceSnapshot {
  ordersSubmitted: number
  ordersFilled: number
  ordersRejected: number
  ordersCancelled: number
  fillRatioPercent: number
  dailyReturnPercent: number
  maxDrawdown: number
  averageExecutionLatencySeconds: number | null
  winRatePercent: number
}
