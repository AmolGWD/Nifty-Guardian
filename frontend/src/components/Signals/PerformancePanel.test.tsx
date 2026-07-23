import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PerformancePanel } from './PerformancePanel'
import * as hooks from '../../hooks'
import type { SignalEngineData } from '../../hooks'

function makeData(overrides: Partial<SignalEngineData> = {}): SignalEngineData {
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
    ...overrides,
  }
}

describe('PerformancePanel', () => {
  it('renders zeroed performance before any trades', () => {
    vi.spyOn(hooks, 'useSignalEngine').mockReturnValue(makeData())
    render(<PerformancePanel />)

    expect(screen.getByText('0.00%')).toBeInTheDocument()
  })

  it('renders win rate and pnl figures from the backend', () => {
    vi.spyOn(hooks, 'useSignalEngine').mockReturnValue(
      makeData({
        performance: {
          openTrades: [],
          closedTrades: [],
          winRate: 66.67,
          todayPnl: 750,
          weeklyPnl: 1200,
          monthlyPnl: 3400,
        },
        report: {
          reportDate: '2026-01-05',
          totalSignals: 3,
          winningTrades: 2,
          losingTrades: 1,
          winRate: 66.67,
          netPoints: 750,
          averageRewardRiskRatio: 2.1,
          bestTrade: null,
          worstTrade: null,
        },
      }),
    )
    render(<PerformancePanel />)

    expect(screen.getByText('66.67%')).toBeInTheDocument()
    expect(screen.getByText('750.00')).toBeInTheDocument()
    expect(screen.getByText('1200.00')).toBeInTheDocument()
    expect(screen.getByText('3400.00')).toBeInTheDocument()
    expect(screen.getByText('2.10')).toBeInTheDocument()
  })
})
