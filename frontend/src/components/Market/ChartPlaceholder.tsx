import { Panel } from '../Common'
import { useMarketData } from '../../hooks'
import styles from './ChartPlaceholder.module.css'

/** Placeholder only - no TradingView, no charting library. A static mock area, swapped for a real chart later. */
export function ChartPlaceholder() {
  const { currentCandle } = useMarketData()

  return (
    <Panel title="Chart">
      <div className={styles.area}>
        {currentCandle
          ? `Chart placeholder - last close ${currentCandle.close.toFixed(2)}`
          : 'Chart placeholder - no candle data yet'}
      </div>
    </Panel>
  )
}
