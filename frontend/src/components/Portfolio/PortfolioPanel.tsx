import { Panel, StatRow, formatCurrency, formatPercent, pnlTone } from '../Common'
import { usePortfolio } from '../../hooks'

/** Cash, Equity, Daily PnL, Drawdown. */
export function PortfolioPanel() {
  const portfolio = usePortfolio()

  return (
    <Panel title="Portfolio">
      <StatRow label="Cash" value={formatCurrency(portfolio.cash)} />
      <StatRow label="Total Equity" value={formatCurrency(portfolio.totalEquity)} />
      <StatRow
        label="Daily PnL"
        value={formatCurrency(portfolio.dailyPnl)}
        tone={pnlTone(portfolio.dailyPnl)}
      />
      <StatRow label="Peak Equity" value={formatCurrency(portfolio.peakEquity)} />
      <StatRow
        label="Drawdown"
        value={formatCurrency(portfolio.drawdown)}
        tone={portfolio.drawdown > 0 ? 'negative' : 'neutral'}
      />
      <StatRow
        label="Drawdown %"
        value={formatPercent(portfolio.drawdownPercent)}
        tone={portfolio.drawdown > 0 ? 'negative' : 'neutral'}
      />
      <StatRow label="Open Positions" value={portfolio.openPositionIds.length} />
    </Panel>
  )
}
