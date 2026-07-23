import { ApiHttpError, ApiNetworkError, ApiTimeoutError } from './api/client'
import type { ApiClientConfig } from './api/client'
import {
  getSignalEngineStatus,
  getSignalPerformance,
  getSignalReportToday,
  getSignalState,
  getSignalTrades,
  postSignalEngineStart,
  postSignalEngineStop,
} from './api/signals'
import {
  mapDailyReport,
  mapDummyTrade,
  mapSignalPerformance,
  mapSignalState,
} from './signalWireMapping'
import type { DailyReport, DummyTrade, SignalEngineState, SignalPerformance } from '../types'

export interface SignalEngineSnapshot {
  state: SignalEngineState
  performance: SignalPerformance
  trades: DummyTrade[]
  report: DailyReport
  running: boolean
}

function emptySnapshot(): SignalEngineSnapshot {
  return {
    state: {
      marketStatus: null,
      marketBias: 'None',
      latestSignalType: null,
      latestGuardianScore: null,
      latestExplanation: null,
      latestSignalAt: null,
      latestEntryPrice: null,
      latestStopLoss: null,
      latestTarget: null,
      signalsSentToday: 0,
    },
    performance: {
      openTrades: [],
      closedTrades: [],
      winRate: 0,
      todayPnl: 0,
      weeklyPnl: 0,
      monthlyPnl: 0,
    },
    trades: [],
    report: {
      reportDate: new Date().toISOString().slice(0, 10),
      totalSignals: 0,
      winningTrades: 0,
      losingTrades: 0,
      winRate: 0,
      netPoints: 0,
      averageRewardRiskRatio: 0,
      bestTrade: null,
      worstTrade: null,
    },
    running: false,
  }
}

function describeError(error: unknown): string {
  if (error instanceof ApiTimeoutError) return `timeout: ${error.message}`
  if (error instanceof ApiNetworkError) return `backend unavailable: ${error.message}`
  if (error instanceof ApiHttpError) return `HTTP ${error.status}: ${error.message}`
  return error instanceof Error ? error.message : 'unknown error'
}

/**
 * Polls every /api/signals/* endpoint on an interval - the same
 * poll-and-swallow-errors discipline `RestDashboardService` (Phase 22,
 * frozen) already established for the Dashboard's own connectivity:
 * a failed tick is logged and swallowed, `getSnapshot()` keeps
 * returning the last known-good snapshot, and the next tick tries
 * again. Start/Stop call the backend directly and immediately refresh.
 */
export class SignalEngineService {
  private readonly apiConfig: ApiClientConfig
  private readonly pollingIntervalMs: number
  private snapshot: SignalEngineSnapshot = emptySnapshot()
  private pollHandle: ReturnType<typeof setInterval> | null = null
  private readonly listeners = new Set<(snapshot: SignalEngineSnapshot) => void>()

  constructor(config: { apiBaseUrl: string; apiTimeoutMs: number; pollingIntervalMs: number }) {
    this.apiConfig = { baseUrl: config.apiBaseUrl, timeoutMs: config.apiTimeoutMs }
    this.pollingIntervalMs = config.pollingIntervalMs
    this.startPolling()
  }

  getSnapshot(): SignalEngineSnapshot {
    return this.snapshot
  }

  subscribe(listener: (snapshot: SignalEngineSnapshot) => void): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  start(): void {
    void this.performAction(() => postSignalEngineStart(this.apiConfig))
  }

  stop(): void {
    void this.performAction(() => postSignalEngineStop(this.apiConfig))
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
      const [status, state, performance, trades, report] = await Promise.all([
        getSignalEngineStatus(this.apiConfig),
        getSignalState(this.apiConfig),
        getSignalPerformance(this.apiConfig),
        getSignalTrades(this.apiConfig),
        getSignalReportToday(this.apiConfig),
      ])
      this.snapshot = {
        running: status.running,
        state: mapSignalState(state),
        performance: mapSignalPerformance(performance),
        trades: trades.map(mapDummyTrade),
        report: mapDailyReport(report),
      }
      this.emit()
    } catch (error) {
      console.warn(`[SignalEngineService] poll failed - ${describeError(error)}`)
    }
  }

  private async performAction(action: () => Promise<unknown>): Promise<void> {
    try {
      await action()
    } catch (error) {
      console.warn(`[SignalEngineService] action failed - ${describeError(error)}`)
    }
    await this.refresh()
  }

  private emit(): void {
    for (const listener of this.listeners) {
      listener(this.snapshot)
    }
  }
}
