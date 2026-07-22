import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MockDashboardService } from './mockDashboardService'
import type { MockDataset, MockTick } from './mockDataset.types'

function makeTick(overrides: Partial<MockTick> = {}): MockTick {
  return {
    candle: {
      timestamp: '2026-01-05T09:15:00',
      open: 100,
      high: 101,
      low: 99,
      close: 100.5,
      volume: 1000,
    },
    marketContext: {
      asOf: '2026-01-05T09:15:00',
      trend: 'BullishTrend',
      momentum: 'StrongMomentum',
      volatility: 'LowVolatility',
      volumeStrength: 'AverageVolume',
      marketBias: 'BullishBias',
      optionChainBias: 'BullishBias',
      sessionState: 'OPEN',
      overallState: 'StrongBullish',
    },
    signal: null,
    riskDecision: null,
    recommendation: null,
    orders: [],
    positions: [],
    portfolio: {
      asOf: '2026-01-05T09:15:00',
      cash: 100_000,
      availableMargin: 100_000,
      openPositionIds: [],
      closedPositionIds: [],
      dailyPnl: 0,
      totalEquity: 100_000,
      peakEquity: 100_000,
      drawdown: 0,
      drawdownPercent: 0,
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
    health: {
      processedCandles: 1,
      averageProcessingLatencySeconds: 0.005,
      uptimeSeconds: 0.05,
      eventsPublished: 1,
      ordersGenerated: 0,
      currentState: 'Running',
    },
    newJournalEntries: [
      {
        entryId: 'entry-1',
        entryType: 'Signal',
        timestamp: '2026-01-05T09:15:00',
        sourceEventId: 'event-1',
        description: 'tick',
      },
    ],
    ...overrides,
  }
}

function makeDataset(tickCount: number): MockDataset {
  return {
    totalCandles: tickCount,
    warmupCandles: 0,
    initialCapital: 100_000,
    replaySpeed: 'Unlimited',
    randomSeed: 1,
    ticks: Array.from({ length: tickCount }, (_, i) =>
      makeTick({
        newJournalEntries: [
          {
            entryId: `entry-${i}`,
            entryType: 'Signal',
            timestamp: '2026-01-05T09:15:00',
            sourceEventId: `event-${i}`,
            description: `tick ${i}`,
          },
        ],
      }),
    ),
  }
}

describe('MockDashboardService', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('starts in NotStarted with an empty snapshot', () => {
    const service = new MockDashboardService(makeDataset(3))
    const snapshot = service.getSnapshot()

    expect(snapshot.runtime.sessionState).toBe('NotStarted')
    expect(snapshot.runtime.processedCandles).toBe(0)
    expect(snapshot.currentCandle).toBeNull()
    expect(snapshot.portfolio.cash).toBe(100_000)
    expect(snapshot.journal).toEqual([])
  })

  it('start() transitions to Running and begins advancing ticks', () => {
    const service = new MockDashboardService(makeDataset(3))
    service.start()

    expect(service.getSnapshot().runtime.sessionState).toBe('Running')

    vi.advanceTimersByTime(50)
    expect(service.getSnapshot().runtime.processedCandles).toBe(1)

    vi.advanceTimersByTime(50)
    expect(service.getSnapshot().runtime.processedCandles).toBe(2)
  })

  it('pause() stops advancing; resume() continues from where it left off', () => {
    const service = new MockDashboardService(makeDataset(5))
    service.start()
    vi.advanceTimersByTime(50)
    expect(service.getSnapshot().runtime.processedCandles).toBe(1)

    service.pause()
    expect(service.getSnapshot().runtime.sessionState).toBe('Paused')
    vi.advanceTimersByTime(200)
    expect(service.getSnapshot().runtime.processedCandles).toBe(1)

    service.resume()
    expect(service.getSnapshot().runtime.sessionState).toBe('Running')
    vi.advanceTimersByTime(50)
    expect(service.getSnapshot().runtime.processedCandles).toBe(2)
  })

  it('stop() halts progress and cannot be resumed', () => {
    const service = new MockDashboardService(makeDataset(5))
    service.start()
    vi.advanceTimersByTime(50)
    service.stop()

    expect(service.getSnapshot().runtime.sessionState).toBe('Stopped')
    vi.advanceTimersByTime(200)
    expect(service.getSnapshot().runtime.processedCandles).toBe(1)
  })

  it('auto-stops once every tick has been consumed', () => {
    const service = new MockDashboardService(makeDataset(2))
    service.start()
    vi.advanceTimersByTime(200)

    expect(service.getSnapshot().runtime.processedCandles).toBe(2)
    expect(service.getSnapshot().runtime.sessionState).toBe('Stopped')
  })

  it('replay() resets progress and journal, then starts again from tick 0', () => {
    const service = new MockDashboardService(makeDataset(3))
    service.start()
    vi.advanceTimersByTime(150)
    expect(service.getSnapshot().journal.length).toBeGreaterThan(0)

    service.replay()
    expect(service.getSnapshot().runtime.processedCandles).toBe(0)
    expect(service.getSnapshot().journal).toEqual([])
    expect(service.getSnapshot().runtime.sessionState).toBe('Running')

    vi.advanceTimersByTime(50)
    expect(service.getSnapshot().runtime.processedCandles).toBe(1)
  })

  it('reset() returns fully to NotStarted with an empty snapshot', () => {
    const service = new MockDashboardService(makeDataset(3))
    service.start()
    vi.advanceTimersByTime(100)

    service.reset()
    const snapshot = service.getSnapshot()
    expect(snapshot.runtime.sessionState).toBe('NotStarted')
    expect(snapshot.runtime.processedCandles).toBe(0)
    expect(snapshot.journal).toEqual([])
  })

  it('journal accumulates newJournalEntries across ticks', () => {
    const service = new MockDashboardService(makeDataset(3))
    service.start()
    vi.advanceTimersByTime(150)

    expect(service.getSnapshot().journal.map((entry) => entry.entryId)).toEqual([
      'entry-0',
      'entry-1',
      'entry-2',
    ])
  })

  it('subscribe() notifies listeners on every tick and unsubscribe stops notifications', () => {
    const service = new MockDashboardService(makeDataset(3))
    const listener = vi.fn()
    const unsubscribe = service.subscribe(listener)

    service.start()
    vi.advanceTimersByTime(50)
    expect(listener).toHaveBeenCalled()

    const callsBeforeUnsubscribe = listener.mock.calls.length
    unsubscribe()
    vi.advanceTimersByTime(50)
    expect(listener.mock.calls.length).toBe(callsBeforeUnsubscribe)
  })
})
