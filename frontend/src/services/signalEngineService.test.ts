import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { SignalEngineService } from './signalEngineService'
import type {
  WireDailyReport,
  WireDummyTrade,
  WireEngineStatus,
  WireSignalPerformance,
  WireSignalState,
} from './api/signalsWireTypes'

const {
  getSignalEngineStatusMock,
  getSignalStateMock,
  getSignalPerformanceMock,
  getSignalTradesMock,
  getSignalReportTodayMock,
  postSignalEngineStartMock,
  postSignalEngineStopMock,
} = vi.hoisted(() => ({
  getSignalEngineStatusMock: vi.fn(),
  getSignalStateMock: vi.fn(),
  getSignalPerformanceMock: vi.fn(),
  getSignalTradesMock: vi.fn(),
  getSignalReportTodayMock: vi.fn(),
  postSignalEngineStartMock: vi.fn(),
  postSignalEngineStopMock: vi.fn(),
}))
vi.mock('./api/signals', () => ({
  getSignalEngineStatus: getSignalEngineStatusMock,
  getSignalState: getSignalStateMock,
  getSignalPerformance: getSignalPerformanceMock,
  getSignalTrades: getSignalTradesMock,
  getSignalReportToday: getSignalReportTodayMock,
  postSignalEngineStart: postSignalEngineStartMock,
  postSignalEngineStop: postSignalEngineStopMock,
}))

function wireStatus(overrides: Partial<WireEngineStatus> = {}): WireEngineStatus {
  return { running: false, live_session_state: null, ...overrides }
}

function wireState(overrides: Partial<WireSignalState> = {}): WireSignalState {
  return {
    market_status: null,
    market_bias: 'None',
    latest_signal_type: null,
    latest_guardian_score: null,
    latest_explanation: null,
    latest_signal_at: null,
    latest_entry_price: null,
    latest_stop_loss: null,
    latest_target: null,
    signals_sent_today: 0,
    ...overrides,
  }
}

function wireTrade(overrides: Partial<WireDummyTrade> = {}): WireDummyTrade {
  return {
    trade_id: 'trade-1',
    strategy_name: 'EMABreakout',
    direction: 'Long',
    guardian_score: { score: 90, strength: 'Strong', reward_risk_ratio: 2, reasons: ['r'] },
    entry_price: 100,
    stop_loss: 95,
    target: 115,
    quantity: 50,
    opened_at: '2026-01-05T09:30:00',
    status: 'Open',
    exit_price: null,
    closed_at: null,
    pnl: null,
    r_multiple: null,
    duration_seconds: null,
    exit_reason: null,
    ...overrides,
  }
}

function wirePerformance(overrides: Partial<WireSignalPerformance> = {}): WireSignalPerformance {
  return {
    open_trades: [],
    closed_trades: [],
    win_rate: 0,
    today_pnl: 0,
    weekly_pnl: 0,
    monthly_pnl: 0,
    ...overrides,
  }
}

function wireReport(overrides: Partial<WireDailyReport> = {}): WireDailyReport {
  return {
    report_date: '2026-01-05',
    total_signals: 0,
    winning_trades: 0,
    losing_trades: 0,
    win_rate: 0,
    net_points: 0,
    average_reward_risk_ratio: 0,
    best_trade: null,
    worst_trade: null,
    ...overrides,
  }
}

const config = { apiBaseUrl: 'http://localhost:8000', apiTimeoutMs: 5000, pollingIntervalMs: 1000 }

function mockAllEndpoints(): void {
  getSignalEngineStatusMock.mockResolvedValue(wireStatus())
  getSignalStateMock.mockResolvedValue(wireState())
  getSignalPerformanceMock.mockResolvedValue(wirePerformance())
  getSignalTradesMock.mockResolvedValue([])
  getSignalReportTodayMock.mockResolvedValue(wireReport())
}

describe('SignalEngineService', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    getSignalEngineStatusMock.mockReset()
    getSignalStateMock.mockReset()
    getSignalPerformanceMock.mockReset()
    getSignalTradesMock.mockReset()
    getSignalReportTodayMock.mockReset()
    postSignalEngineStartMock.mockReset()
    postSignalEngineStopMock.mockReset()
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('starts with an empty, not-running snapshot before the first poll resolves', () => {
    getSignalEngineStatusMock.mockReturnValue(new Promise(() => {}))
    getSignalStateMock.mockReturnValue(new Promise(() => {}))
    getSignalPerformanceMock.mockReturnValue(new Promise(() => {}))
    getSignalTradesMock.mockReturnValue(new Promise(() => {}))
    getSignalReportTodayMock.mockReturnValue(new Promise(() => {}))

    const service = new SignalEngineService(config)

    expect(service.getSnapshot().running).toBe(false)
    expect(service.getSnapshot().trades).toEqual([])
    service.stopPolling()
  })

  it('polls immediately on construction and maps every response', async () => {
    mockAllEndpoints()
    getSignalStateMock.mockResolvedValue(wireState({ market_bias: 'Long', signals_sent_today: 1 }))
    getSignalTradesMock.mockResolvedValue([wireTrade()])

    const service = new SignalEngineService(config)

    await vi.waitFor(() => expect(service.getSnapshot().trades).toHaveLength(1))
    expect(service.getSnapshot().state.marketBias).toBe('Long')
    expect(service.getSnapshot().state.signalsSentToday).toBe(1)
    expect(service.getSnapshot().trades[0]?.tradeId).toBe('trade-1')
    service.stopPolling()
  })

  it('keeps the last known-good snapshot when a poll fails', async () => {
    mockAllEndpoints()
    getSignalTradesMock.mockResolvedValue([wireTrade({ trade_id: 'trade-A' })])
    const service = new SignalEngineService(config)
    await vi.waitFor(() => expect(service.getSnapshot().trades).toHaveLength(1))

    getSignalStateMock.mockRejectedValue(new Error('network down'))
    await vi.advanceTimersByTimeAsync(1000)

    expect(service.getSnapshot().trades[0]?.tradeId).toBe('trade-A')
    expect(console.warn).toHaveBeenCalled()
    service.stopPolling()
  })

  it('start() calls the start endpoint then immediately refreshes', async () => {
    mockAllEndpoints()
    postSignalEngineStartMock.mockResolvedValue(wireStatus({ running: true }))
    const service = new SignalEngineService(config)
    await vi.waitFor(() => expect(getSignalStateMock).toHaveBeenCalled())

    getSignalStateMock.mockClear()
    service.start()

    await vi.waitFor(() => {
      expect(postSignalEngineStartMock).toHaveBeenCalledTimes(1)
      expect(getSignalStateMock).toHaveBeenCalledTimes(1)
    })
    service.stopPolling()
  })

  it('stop() calls the stop endpoint then immediately refreshes', async () => {
    mockAllEndpoints()
    postSignalEngineStopMock.mockResolvedValue(wireStatus({ running: false }))
    const service = new SignalEngineService(config)
    await vi.waitFor(() => expect(getSignalStateMock).toHaveBeenCalled())

    getSignalStateMock.mockClear()
    service.stop()

    await vi.waitFor(() => {
      expect(postSignalEngineStopMock).toHaveBeenCalledTimes(1)
      expect(getSignalStateMock).toHaveBeenCalledTimes(1)
    })
    service.stopPolling()
  })

  it('notifies subscribers on each successful poll', async () => {
    mockAllEndpoints()
    const service = new SignalEngineService(config)
    await vi.waitFor(() => expect(getSignalStateMock).toHaveBeenCalled())

    const listener = vi.fn()
    service.subscribe(listener)
    await vi.advanceTimersByTimeAsync(1000)

    expect(listener).toHaveBeenCalled()
    service.stopPolling()
  })

  it('stopPolling() stops further polling', async () => {
    mockAllEndpoints()
    const service = new SignalEngineService(config)
    await vi.waitFor(() => expect(getSignalStateMock).toHaveBeenCalled())

    service.stopPolling()
    const callsAtStop = getSignalStateMock.mock.calls.length
    await vi.advanceTimersByTimeAsync(3000)

    expect(getSignalStateMock.mock.calls.length).toBe(callsAtStop)
  })
})
