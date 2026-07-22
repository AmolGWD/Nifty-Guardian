import { ApiHttpError, ApiNetworkError, ApiTimeoutError } from './api/client'
import type { ApiClientConfig } from './api/client'
import { getDashboardSnapshot } from './api/dashboard'
import {
  postRuntimePause,
  postRuntimeReplay,
  postRuntimeResume,
  postRuntimeStart,
  postRuntimeStop,
} from './api/runtime'
import type { WireRuntimeStats } from './api/wireTypes'
import type { DashboardConfig } from './config'
import type { DashboardService } from './dashboardService'
import { mapDashboardSnapshot } from './wireMapping'
import type { DashboardSnapshot, Portfolio } from '../types'

function emptyPortfolio(initialCapital: number): Portfolio {
  return {
    asOf: new Date(0).toISOString(),
    cash: initialCapital,
    availableMargin: initialCapital,
    openPositionIds: [],
    closedPositionIds: [],
    dailyPnl: 0,
    totalEquity: initialCapital,
    peakEquity: initialCapital,
    drawdown: 0,
    drawdownPercent: 0,
  }
}

function emptySnapshot(): DashboardSnapshot {
  return {
    runtime: {
      sessionState: 'NotStarted',
      replaySpeed: 'Unlimited',
      processedCandles: 0,
      totalCandles: 0,
      eventsPublished: 0,
      ordersGenerated: 0,
      uptimeSeconds: 0,
    },
    currentCandle: null,
    marketContext: null,
    latestSignal: null,
    latestRiskDecision: null,
    latestRecommendation: null,
    orders: [],
    positions: [],
    portfolio: emptyPortfolio(100_000),
    journal: [],
    health: {
      processedCandles: 0,
      averageProcessingLatencySeconds: null,
      uptimeSeconds: 0,
      eventsPublished: 0,
      ordersGenerated: 0,
      currentState: 'NotStarted',
    },
    performance: {
      ordersSubmitted: 0,
      ordersFilled: 0,
      ordersRejected: 0,
      ordersCancelled: 0,
      fillRatioPercent: 0,
      dailyReturnPercent: 0,
      maxDrawdown: 0,
      averageExecutionLatencySeconds: null,
      winRatePercent: 0,
    },
  }
}

function describeError(error: unknown): string {
  if (error instanceof ApiTimeoutError) return `timeout: ${error.message}`
  if (error instanceof ApiNetworkError) return `backend unavailable: ${error.message}`
  if (error instanceof ApiHttpError) return `HTTP ${error.status}: ${error.message}`
  return error instanceof Error ? error.message : 'unknown error'
}

/**
 * Polls GET /api/dashboard on an interval (`pollingIntervalMs`, default
 * 1000ms per the CTO brief - no WebSocket this phase) and maps every
 * response into the same `DashboardSnapshot` shape `MockDashboardService`
 * produces, so the (frozen) store/components never know which service
 * they're reading from.
 *
 * Error handling is entirely internal, by design (the CTO brief's "No
 * component changes" - there is no new UI surface for connection
 * status this phase): a failed poll (timeout, network error, non-2xx
 * backend response) is logged and swallowed, `getSnapshot()` keeps
 * returning the last known-good snapshot, and the next interval tick
 * tries again - graceful retry is simply "the loop never stops itself
 * on a single failed tick."
 */
export class RestDashboardService implements DashboardService {
  private readonly apiConfig: ApiClientConfig
  private readonly pollingIntervalMs: number
  private readonly defaultReplaySpeed: string
  private snapshot: DashboardSnapshot = emptySnapshot()
  private pollHandle: ReturnType<typeof setInterval> | null = null
  private readonly listeners = new Set<(snapshot: DashboardSnapshot) => void>()

  constructor(config: DashboardConfig) {
    this.apiConfig = { baseUrl: config.apiBaseUrl, timeoutMs: config.apiTimeoutMs }
    this.pollingIntervalMs = config.pollingIntervalMs
    this.defaultReplaySpeed = config.defaultReplaySpeed
    this.startPolling()
  }

  getSnapshot(): DashboardSnapshot {
    return this.snapshot
  }

  subscribe(listener: (snapshot: DashboardSnapshot) => void): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  start(): void {
    void this.performAction(() => postRuntimeStart(this.apiConfig))
  }

  pause(): void {
    void this.performAction(() => postRuntimePause(this.apiConfig))
  }

  resume(): void {
    void this.performAction(() => postRuntimeResume(this.apiConfig))
  }

  stop(): void {
    void this.performAction(() => postRuntimeStop(this.apiConfig))
  }

  replay(): void {
    void this.performAction(() =>
      postRuntimeReplay(this.apiConfig, {
        replay_speed: this.defaultReplaySpeed,
        maximum_candles: null,
      }),
    )
  }

  reset(): void {
    // Honest gap, not a silent no-op pretending to work: the CTO
    // brief's endpoint list (GET dashboard/health/state, POST start/
    // pause/resume/stop/replay) has no reset equivalent - there is no
    // backend operation this can call yet. Logged clearly rather than
    // guessed at (mapping it to stop() or replay() would silently
    // change what "Reset" means to whoever clicks the button). See
    // docs/API_GUIDE.md.
    console.warn(
      '[RestDashboardService] reset() has no backend endpoint yet - this is a known, documented gap (see docs/API_GUIDE.md), not a failure.',
    )
  }

  stopPolling(): void {
    if (this.pollHandle !== null) {
      clearInterval(this.pollHandle)
      this.pollHandle = null
    }
  }

  private startPolling(): void {
    void this.refresh()
    this.pollHandle = setInterval(() => {
      void this.refresh()
    }, this.pollingIntervalMs)
  }

  private async refresh(): Promise<void> {
    try {
      const wireSnapshot = await getDashboardSnapshot(this.apiConfig)
      this.snapshot = mapDashboardSnapshot(wireSnapshot)
      this.emit()
    } catch (error) {
      console.warn(`[RestDashboardService] poll failed - ${describeError(error)}`)
    }
  }

  private async performAction(action: () => Promise<WireRuntimeStats>): Promise<void> {
    try {
      await action()
    } catch (error) {
      console.warn(`[RestDashboardService] action failed - ${describeError(error)}`)
    }
    await this.refresh()
  }

  private emit(): void {
    for (const listener of this.listeners) {
      listener(this.snapshot)
    }
  }
}
