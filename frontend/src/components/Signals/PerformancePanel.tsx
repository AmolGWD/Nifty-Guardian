import { Panel, StatRow, formatPercent, pnlColor } from '../Common'
import { useSignalEngine } from '../../hooks'

/** Win Rate, Today's PnL, Weekly PnL, Monthly PnL - and today's end-of-day report summary. */
export function PerformancePanel() {
  const { performance, report } = useSignalEngine()

  return (
    <Panel title="Performance">
      <StatRow label="Win Rate" value={formatPercent(performance.winRate)} />
      <StatRow
        label="Today's PnL"
        value={
          <span style={{ color: pnlColor(performance.todayPnl) }}>
            {performance.todayPnl.toFixed(2)}
          </span>
        }
      />
      <StatRow
        label="Weekly PnL"
        value={
          <span style={{ color: pnlColor(performance.weeklyPnl) }}>
            {performance.weeklyPnl.toFixed(2)}
          </span>
        }
      />
      <StatRow
        label="Monthly PnL"
        value={
          <span style={{ color: pnlColor(performance.monthlyPnl) }}>
            {performance.monthlyPnl.toFixed(2)}
          </span>
        }
      />

      <StatRow label="Total Signals (Today)" value={report.totalSignals} />
      <StatRow label="Winning Trades" value={report.winningTrades} />
      <StatRow label="Losing Trades" value={report.losingTrades} />
      <StatRow label="Average RR" value={report.averageRewardRiskRatio.toFixed(2)} />
    </Panel>
  )
}
