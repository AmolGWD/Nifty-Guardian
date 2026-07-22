import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PortfolioPanel } from './PortfolioPanel'
import * as hooks from '../../hooks'
import type { Portfolio } from '../../types'

function mockPortfolio(overrides: Partial<Portfolio> = {}) {
  const portfolio: Portfolio = {
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
    ...overrides,
  }
  vi.spyOn(hooks, 'usePortfolio').mockReturnValue(portfolio)
  return portfolio
}

describe('PortfolioPanel', () => {
  it('renders cash, equity, daily PnL, and drawdown from the store', () => {
    mockPortfolio({ cash: 104_680, totalEquity: 105_755, dailyPnl: 4_680, drawdown: 0 })
    render(<PortfolioPanel />)

    expect(screen.getByText('1,04,680.00')).toBeInTheDocument()
    expect(screen.getByText('1,05,755.00')).toBeInTheDocument()
    expect(screen.getByText('4,680.00')).toBeInTheDocument()
  })

  it('shows the open position count', () => {
    mockPortfolio({ openPositionIds: ['pos-1'] })
    render(<PortfolioPanel />)

    expect(screen.getByText('1')).toBeInTheDocument()
  })
})
