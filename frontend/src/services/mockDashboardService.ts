import dataset from '../../../scripts/dashboard_mock_data.json'
import type { DashboardSnapshot, JournalEntry, Portfolio, ReplaySpeed } from '../types'
import type { DashboardService } from './dashboardService'
import type { MockDataset } from './mockDataset.types'

const mockDataset = dataset as MockDataset

/**
 * Wall-clock delay between ticks. This is a UI pacing choice, not the
 * backend's `sleep_seconds_for()` - the real `Unlimited` replay speed
 * means "zero delay, process as fast as possible" (see
 * docs/ENGINE_RUNTIME.md); a literal 0ms interval here would jump
 * straight to the final tick with nothing to watch, defeating the
 * point of a "replay progress" console. `TICK_INTERVALS_MS` scales the
 * same way the backend's multipliers do, just against a UI-sized base.
 */
const BASE_INTERVAL_MS = 600
const TICK_INTERVALS_MS: Record<ReplaySpeed, number> = {
  '1x': BASE_INTERVAL_MS,
  '2x': BASE_INTERVAL_MS / 2,
  '5x': BASE_INTERVAL_MS / 5,
  '10x': BASE_INTERVAL_MS / 10,
  Unlimited: 50,
}

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

export class MockDashboardService implements DashboardService {
  private readonly dataset: MockDataset
  private tickIndex = -1
  private sessionState: DashboardSnapshot['runtime']['sessionState'] = 'NotStarted'
  private journal: JournalEntry[] = []
  private intervalHandle: ReturnType<typeof setInterval> | null = null
  private startedAt: number | null = null
  private readonly listeners = new Set<(snapshot: DashboardSnapshot) => void>()

  constructor(data: MockDataset = mockDataset) {
    this.dataset = data
  }

  getSnapshot(): DashboardSnapshot {
    const tick = this.tickIndex >= 0 ? this.dataset.ticks[this.tickIndex] : null

    return {
      runtime: {
        sessionState: this.sessionState,
        replaySpeed: this.dataset.replaySpeed,
        processedCandles: this.tickIndex + 1,
        totalCandles: this.dataset.totalCandles,
        eventsPublished: tick?.health.eventsPublished ?? 0,
        ordersGenerated: tick?.health.ordersGenerated ?? 0,
        uptimeSeconds: this.startedAt === null ? 0 : (Date.now() - this.startedAt) / 1000,
      },
      currentCandle: tick?.candle ?? null,
      marketContext: tick?.marketContext ?? null,
      latestSignal: tick?.signal ?? null,
      latestRiskDecision: tick?.riskDecision ?? null,
      latestRecommendation: tick?.recommendation ?? null,
      orders: tick?.orders ?? [],
      positions: tick?.positions ?? [],
      portfolio: tick?.portfolio ?? emptyPortfolio(this.dataset.initialCapital),
      journal: this.journal,
      health: tick?.health ?? {
        processedCandles: 0,
        averageProcessingLatencySeconds: null,
        uptimeSeconds: 0,
        eventsPublished: 0,
        ordersGenerated: 0,
        currentState: this.sessionState,
      },
      performance: tick?.performance ?? {
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

  subscribe(listener: (snapshot: DashboardSnapshot) => void): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  start(): void {
    if (this.sessionState !== 'NotStarted') return
    this.sessionState = 'Running'
    this.startedAt = Date.now()
    this.runInterval()
    this.emit()
  }

  pause(): void {
    if (this.sessionState !== 'Running') return
    this.sessionState = 'Paused'
    this.clearInterval()
    this.emit()
  }

  resume(): void {
    if (this.sessionState !== 'Paused') return
    this.sessionState = 'Running'
    this.runInterval()
    this.emit()
  }

  stop(): void {
    if (this.sessionState !== 'Running' && this.sessionState !== 'Paused') return
    this.sessionState = 'Stopped'
    this.clearInterval()
    this.emit()
  }

  replay(): void {
    this.clearInterval()
    this.tickIndex = -1
    this.journal = []
    this.sessionState = 'Running'
    this.startedAt = Date.now()
    this.runInterval()
    this.emit()
  }

  reset(): void {
    this.clearInterval()
    this.tickIndex = -1
    this.journal = []
    this.sessionState = 'NotStarted'
    this.startedAt = null
    this.emit()
  }

  private runInterval(): void {
    this.clearInterval()
    const intervalMs = TICK_INTERVALS_MS[this.dataset.replaySpeed]
    this.intervalHandle = setInterval(() => {
      this.advanceTick()
    }, intervalMs)
  }

  private advanceTick(): void {
    if (this.tickIndex >= this.dataset.ticks.length - 1) {
      this.sessionState = 'Stopped'
      this.clearInterval()
      this.emit()
      return
    }
    this.tickIndex += 1
    const tick = this.dataset.ticks[this.tickIndex]
    this.journal = [...this.journal, ...tick.newJournalEntries]
    this.emit()
  }

  private clearInterval(): void {
    if (this.intervalHandle !== null) {
      clearInterval(this.intervalHandle)
      this.intervalHandle = null
    }
  }

  private emit(): void {
    const snapshot = this.getSnapshot()
    for (const listener of this.listeners) {
      listener(snapshot)
    }
  }
}
