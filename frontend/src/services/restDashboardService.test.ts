import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { RestDashboardService } from './restDashboardService'
import type { DashboardConfig } from './config'
import type { WireDashboardSnapshot } from './api/wireTypes'

const { getDashboardSnapshotMock } = vi.hoisted(() => ({
  getDashboardSnapshotMock: vi.fn(),
}))
vi.mock('./api/dashboard', () => ({
  getDashboardSnapshot: getDashboardSnapshotMock,
}))

const {
  postRuntimeStartMock,
  postRuntimePauseMock,
  postRuntimeResumeMock,
  postRuntimeStopMock,
  postRuntimeReplayMock,
} = vi.hoisted(() => ({
  postRuntimeStartMock: vi.fn(),
  postRuntimePauseMock: vi.fn(),
  postRuntimeResumeMock: vi.fn(),
  postRuntimeStopMock: vi.fn(),
  postRuntimeReplayMock: vi.fn(),
}))
vi.mock('./api/runtime', () => ({
  postRuntimeStart: postRuntimeStartMock,
  postRuntimePause: postRuntimePauseMock,
  postRuntimeResume: postRuntimeResumeMock,
  postRuntimeStop: postRuntimeStopMock,
  postRuntimeReplay: postRuntimeReplayMock,
}))

function wireSnapshot(overrides: Partial<WireDashboardSnapshot> = {}): WireDashboardSnapshot {
  return {
    runtime: {
      session_state: 'Running',
      replay_speed: '1x',
      processed_candles: 3,
      total_candles: 75,
      events_published: 5,
      orders_generated: 0,
      uptime_seconds: 1.5,
    },
    current_candle: null,
    market_context: null,
    latest_signal: null,
    latest_risk_decision: null,
    latest_recommendation: null,
    orders: [],
    positions: [],
    portfolio: {
      as_of: '2026-01-05T09:15:00',
      cash: 100_000,
      available_margin: 100_000,
      open_position_ids: [],
      closed_position_ids: [],
      daily_pnl: 0,
      total_equity: 100_000,
      peak_equity: 100_000,
      drawdown: 0,
      drawdown_percent: 0,
    },
    journal: [],
    health: {
      processed_candles: 3,
      average_processing_latency_seconds: 0.01,
      uptime_seconds: 1.5,
      events_published: 5,
      orders_generated: 0,
      current_state: 'Running',
    },
    performance: {
      orders_submitted: 0,
      orders_filled: 0,
      orders_rejected: 0,
      orders_cancelled: 0,
      fill_ratio_percent: 0,
      daily_return_percent: 0,
      max_drawdown: 0,
      average_execution_latency_seconds: null,
      win_rate_percent: 0,
    },
    ...overrides,
  }
}

const config: DashboardConfig = {
  serviceMode: 'rest',
  apiBaseUrl: 'http://localhost:8000',
  pollingIntervalMs: 1000,
  apiTimeoutMs: 5000,
  defaultReplaySpeed: '1x',
}

describe('RestDashboardService', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    getDashboardSnapshotMock.mockReset()
    postRuntimeStartMock.mockReset()
    postRuntimePauseMock.mockReset()
    postRuntimeResumeMock.mockReset()
    postRuntimeStopMock.mockReset()
    postRuntimeReplayMock.mockReset()
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('starts with an empty NotStarted snapshot before the first poll resolves', () => {
    getDashboardSnapshotMock.mockReturnValue(new Promise(() => {}))
    const service = new RestDashboardService(config)

    expect(service.getSnapshot().runtime.sessionState).toBe('NotStarted')
    service.stopPolling()
  })

  it('polls immediately on construction and maps the response', async () => {
    getDashboardSnapshotMock.mockResolvedValue(wireSnapshot())
    const service = new RestDashboardService(config)

    await vi.waitFor(() => {
      expect(service.getSnapshot().runtime.processedCandles).toBe(3)
    })
    expect(service.getSnapshot().runtime.sessionState).toBe('Running')
    service.stopPolling()
  })

  it('polls again after pollingIntervalMs and notifies subscribers', async () => {
    getDashboardSnapshotMock.mockResolvedValue(
      wireSnapshot({ runtime: { ...wireSnapshot().runtime, processed_candles: 1 } }),
    )
    const service = new RestDashboardService(config)
    await vi.waitFor(() => expect(service.getSnapshot().runtime.processedCandles).toBe(1))

    const listener = vi.fn()
    service.subscribe(listener)

    getDashboardSnapshotMock.mockResolvedValue(
      wireSnapshot({ runtime: { ...wireSnapshot().runtime, processed_candles: 2 } }),
    )
    await vi.advanceTimersByTimeAsync(1000)

    expect(service.getSnapshot().runtime.processedCandles).toBe(2)
    expect(listener).toHaveBeenCalled()
    service.stopPolling()
  })

  it('keeps the last known-good snapshot when a poll fails (graceful retry)', async () => {
    getDashboardSnapshotMock.mockResolvedValue(
      wireSnapshot({ runtime: { ...wireSnapshot().runtime, processed_candles: 7 } }),
    )
    const service = new RestDashboardService(config)
    await vi.waitFor(() => expect(service.getSnapshot().runtime.processedCandles).toBe(7))

    getDashboardSnapshotMock.mockRejectedValue(new Error('network down'))
    await vi.advanceTimersByTimeAsync(1000)

    // Snapshot is unchanged - not cleared, not crashed.
    expect(service.getSnapshot().runtime.processedCandles).toBe(7)
    expect(console.warn).toHaveBeenCalled()
    service.stopPolling()
  })

  it('recovers automatically once polling succeeds again', async () => {
    getDashboardSnapshotMock.mockRejectedValue(new Error('backend unavailable'))
    const service = new RestDashboardService(config)
    await vi.waitFor(() => expect(console.warn).toHaveBeenCalled())

    getDashboardSnapshotMock.mockResolvedValue(
      wireSnapshot({ runtime: { ...wireSnapshot().runtime, processed_candles: 9 } }),
    )
    await vi.advanceTimersByTimeAsync(1000)

    expect(service.getSnapshot().runtime.processedCandles).toBe(9)
    service.stopPolling()
  })

  it('start() calls the start endpoint then immediately refreshes', async () => {
    getDashboardSnapshotMock.mockResolvedValue(wireSnapshot())
    postRuntimeStartMock.mockResolvedValue({})
    const service = new RestDashboardService(config)
    await vi.waitFor(() => expect(getDashboardSnapshotMock).toHaveBeenCalled())

    getDashboardSnapshotMock.mockClear()
    service.start()

    await vi.waitFor(() => {
      expect(postRuntimeStartMock).toHaveBeenCalledTimes(1)
      expect(getDashboardSnapshotMock).toHaveBeenCalledTimes(1)
    })
    service.stopPolling()
  })

  it('an action that fails still triggers a refresh afterward', async () => {
    getDashboardSnapshotMock.mockResolvedValue(wireSnapshot())
    postRuntimePauseMock.mockRejectedValue(new Error('409 conflict'))
    const service = new RestDashboardService(config)
    await vi.waitFor(() => expect(getDashboardSnapshotMock).toHaveBeenCalled())

    getDashboardSnapshotMock.mockClear()
    service.pause()

    await vi.waitFor(() => {
      expect(postRuntimePauseMock).toHaveBeenCalledTimes(1)
      expect(getDashboardSnapshotMock).toHaveBeenCalledTimes(1)
    })
    expect(console.warn).toHaveBeenCalled()
    service.stopPolling()
  })

  it('replay() sends the configured default replay speed', async () => {
    getDashboardSnapshotMock.mockResolvedValue(wireSnapshot())
    postRuntimeReplayMock.mockResolvedValue({})
    const service = new RestDashboardService({ ...config, defaultReplaySpeed: '5x' })
    await vi.waitFor(() => expect(getDashboardSnapshotMock).toHaveBeenCalled())

    service.replay()

    await vi.waitFor(() => expect(postRuntimeReplayMock).toHaveBeenCalled())
    expect(postRuntimeReplayMock).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ replay_speed: '5x' }),
    )
    service.stopPolling()
  })

  it('reset() logs a known-gap warning and does not throw', async () => {
    getDashboardSnapshotMock.mockResolvedValue(wireSnapshot())
    const service = new RestDashboardService(config)
    await vi.waitFor(() => expect(getDashboardSnapshotMock).toHaveBeenCalled())

    expect(() => service.reset()).not.toThrow()
    expect(console.warn).toHaveBeenCalledWith(expect.stringContaining('no backend endpoint'))
    service.stopPolling()
  })

  it('stopPolling() stops further GET /api/dashboard calls', async () => {
    getDashboardSnapshotMock.mockResolvedValue(wireSnapshot())
    const service = new RestDashboardService(config)
    await vi.waitFor(() => expect(getDashboardSnapshotMock).toHaveBeenCalled())

    service.stopPolling()
    const callsAtStop = getDashboardSnapshotMock.mock.calls.length
    await vi.advanceTimersByTimeAsync(3000)

    expect(getDashboardSnapshotMock.mock.calls.length).toBe(callsAtStop)
  })
})
