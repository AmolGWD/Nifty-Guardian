import { Badge, Panel, StatRow, formatPercent, formatSeconds, pnlColor } from '../Common'
import { useSignalEngine } from '../../hooks'

/**
 * Win Rate, Today's/Weekly/Monthly PnL, and Today's Summary - the
 * end-of-day report `app.signals.dummy_trade_tracker.build_daily_report()`
 * already builds from the closed-trade history, nothing recomputed here.
 */
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
      <StatRow label="BUY CE" value={report.buyCeCount} />
      <StatRow label="BUY PE" value={report.buyPeCount} />
      <StatRow label="Winning Trades" value={report.winningTrades} />
      <StatRow label="Losing Trades" value={report.losingTrades} />
      <StatRow
        label="Total PnL"
        value={
          <span style={{ color: pnlColor(report.netPoints) }}>{report.netPoints.toFixed(2)}</span>
        }
      />
      <StatRow
        label="Average PnL"
        value={
          <span style={{ color: pnlColor(report.averagePnl) }}>{report.averagePnl.toFixed(2)}</span>
        }
      />
      <StatRow label="Average RR" value={report.averageRewardRiskRatio.toFixed(2)} />
      {report.bestTrade && (
        <StatRow label="Best Trade" value={(report.bestTrade.pnl ?? 0).toFixed(2)} />
      )}
      {report.worstTrade && (
        <StatRow label="Worst Trade" value={(report.worstTrade.pnl ?? 0).toFixed(2)} />
      )}
      <StatRow label="Highest Guardian Score" value={report.highestGuardianScore.toFixed(1)} />
      <StatRow label="Average Hold Time" value={formatSeconds(report.averageHoldTimeSeconds)} />
      <StatRow label="Market Bias" value={<Badge tone="neutral">{report.marketBias}</Badge>} />
      <StatRow
        label="Guardian Status"
        value={
          <Badge tone={report.guardianStatus === 'Active' ? 'positive' : 'neutral'}>
            {report.guardianStatus}
          </Badge>
        }
      />
    </Panel>
  )
}
