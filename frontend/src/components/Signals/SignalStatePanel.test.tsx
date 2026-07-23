import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SignalStatePanel } from './SignalStatePanel'
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

describe('SignalStatePanel', () => {
  it('renders the empty state when there is no signal yet', () => {
    vi.spyOn(hooks, 'useSignalEngine').mockReturnValue(makeData())
    render(<SignalStatePanel />)

    expect(screen.getByText('No signal yet.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start Signals' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Stop Signals' })).toBeDisabled()
  })

  it('shows the Guardian Score, confidence, entry/SL/target, and reasons for the latest signal', () => {
    vi.spyOn(hooks, 'useSignalEngine').mockReturnValue(
      makeData({
        running: true,
        state: {
          marketStatus: 'Open',
          marketBias: 'Long',
          latestSignalType: 'BuyCE',
          latestGuardianScore: {
            score: 90,
            strength: 'Strong',
            rewardRiskRatio: 2,
            reasons: ['EMA alignment: price above EMA'],
          },
          latestExplanation: 'EMA alignment: price above EMA',
          latestSignalAt: '2026-01-05T09:30:00',
          latestEntryPrice: 168.0,
          latestStopLoss: 162.0,
          latestTarget: 180.0,
          signalsSentToday: 1,
        },
      }),
    )
    render(<SignalStatePanel />)

    expect(screen.getByText('Open')).toBeInTheDocument()
    expect(screen.getByText('BuyCE')).toBeInTheDocument()
    expect(screen.getByText('90.0')).toBeInTheDocument()
    expect(screen.getByText('Strong')).toBeInTheDocument()
    expect(screen.getByText('168.00')).toBeInTheDocument()
    expect(screen.getByText('162.00')).toBeInTheDocument()
    expect(screen.getByText('180.00')).toBeInTheDocument()
    expect(screen.getByText('EMA alignment: price above EMA')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start Signals' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Stop Signals' })).toBeEnabled()
  })

  it('calls start/stop when the buttons are clicked', () => {
    const start = vi.fn()
    const stop = vi.fn()
    vi.spyOn(hooks, 'useSignalEngine').mockReturnValue(makeData({ start, stop }))
    render(<SignalStatePanel />)

    screen.getByRole('button', { name: 'Start Signals' }).click()
    expect(start).toHaveBeenCalledTimes(1)
  })
})
