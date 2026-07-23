import { describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { DummyTradesPanel } from './DummyTradesPanel'
import * as hooks from '../../hooks'
import type { SignalEngineData } from '../../hooks'
import type { DummyTrade } from '../../types'

function makeTrade(overrides: Partial<DummyTrade> = {}): DummyTrade {
  return {
    tradeId: 'trade-1',
    strategyName: 'EMABreakout',
    direction: 'Long',
    guardianScore: { score: 90, strength: 'Strong', rewardRiskRatio: 2, reasons: ['r'] },
    entryPrice: 100,
    stopLoss: 95,
    target: 115,
    quantity: 50,
    openedAt: '2026-01-05T09:30:00',
    status: 'Open',
    exitPrice: null,
    closedAt: null,
    pnl: null,
    rMultiple: null,
    durationSeconds: null,
    exitReason: null,
    ...overrides,
  }
}

function makeData(trades: DummyTrade[]): SignalEngineData {
  return {
    running: false,
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
      telegramStatus: null,
    },
    performance: {
      openTrades: [],
      closedTrades: [],
      winRate: 0,
      todayPnl: 0,
      weeklyPnl: 0,
      monthlyPnl: 0,
    },
    trades,
    report: {
      reportDate: '2026-01-05',
      totalSignals: 0,
      winningTrades: 0,
      losingTrades: 0,
      winRate: 0,
      netPoints: 0,
      averageRewardRiskRatio: 0,
      bestTrade: null,
      worstTrade: null,
    },
    start: vi.fn(),
    stop: vi.fn(),
  }
}

describe('DummyTradesPanel', () => {
  it('shows empty states when there are no trades at all', () => {
    vi.spyOn(hooks, 'useSignalEngine').mockReturnValue(makeData([]))
    render(<DummyTradesPanel />)

    expect(screen.getByText('No open dummy trade.')).toBeInTheDocument()
    expect(screen.getByText('No closed trades yet.')).toBeInTheDocument()
  })

  it('shows the open dummy trade details, including its status', () => {
    vi.spyOn(hooks, 'useSignalEngine').mockReturnValue(makeData([makeTrade({ status: 'Open' })]))
    render(<DummyTradesPanel />)

    expect(screen.getByText('Open')).toBeInTheDocument()
    expect(screen.getByText('100.00')).toBeInTheDocument()
    expect(screen.getByText('95.00')).toBeInTheDocument()
    expect(screen.getByText('115.00')).toBeInTheDocument()
  })

  it('lists closed trades with status, pnl, duration, r-multiple, and exit reason', () => {
    vi.spyOn(hooks, 'useSignalEngine').mockReturnValue(
      makeData([
        makeTrade({
          tradeId: 'trade-2',
          status: 'Closed',
          exitPrice: 115,
          pnl: 750,
          rMultiple: 3,
          durationSeconds: 5400,
          exitReason: 'Target',
          closedAt: '2026-01-05T11:00:00',
        }),
      ]),
    )
    render(<DummyTradesPanel />)

    const table = screen.getByRole('table')
    expect(within(table).getByText('Closed')).toBeInTheDocument()
    expect(within(table).getByText('750.00')).toBeInTheDocument()
    expect(within(table).getByText('5400.00s')).toBeInTheDocument()
    expect(within(table).getByText('3.00')).toBeInTheDocument()
    expect(within(table).getByText('Target')).toBeInTheDocument()
  })
})
