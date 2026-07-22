import { EmptyState, Panel, StatRow, formatDateTime, formatNumber } from '../Common'
import { useMarketData } from '../../hooks'

/** Current Candle (Timestamp, OHLC, Volume) + Market Context. */
export function MarketPanel() {
  const { currentCandle, marketContext } = useMarketData()

  if (!currentCandle || !marketContext) {
    return (
      <Panel title="Market">
        <EmptyState message="No market data yet - start the engine." />
      </Panel>
    )
  }

  return (
    <Panel title="Market">
      <StatRow label="Timestamp" value={formatDateTime(currentCandle.timestamp)} />
      <StatRow label="Open" value={currentCandle.open.toFixed(2)} />
      <StatRow label="High" value={currentCandle.high.toFixed(2)} />
      <StatRow label="Low" value={currentCandle.low.toFixed(2)} />
      <StatRow label="Close" value={currentCandle.close.toFixed(2)} />
      <StatRow label="Volume" value={formatNumber(currentCandle.volume)} />
      <StatRow label="Trend" value={marketContext.trend} />
      <StatRow label="Momentum" value={marketContext.momentum} />
      <StatRow label="Volatility" value={marketContext.volatility} />
      <StatRow label="Overall State" value={marketContext.overallState} />
    </Panel>
  )
}
