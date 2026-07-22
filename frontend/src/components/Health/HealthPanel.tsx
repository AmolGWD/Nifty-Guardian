import { Badge, Panel, StatRow, formatNumber, formatPercent, sessionStateTone } from '../Common'
import { useHealth } from '../../hooks'

/**
 * Processing Latency, Orders Generated, Fill Ratio, Events, Engine
 * Health. "Engine Health" is a presentational label over the backend's
 * own `currentState` (app.runtime.health.HealthSnapshot, frozen) -
 * this panel does not compute a separate health score.
 */
export function HealthPanel() {
  const { health, performance } = useHealth()

  return (
    <Panel title="Health">
      <StatRow
        label="Processing Latency"
        value={
          health.averageProcessingLatencySeconds === null
            ? '-'
            : `${(health.averageProcessingLatencySeconds * 1000).toFixed(1)}ms`
        }
      />
      <StatRow label="Orders Generated" value={formatNumber(health.ordersGenerated)} />
      <StatRow label="Fill Ratio" value={formatPercent(performance.fillRatioPercent)} />
      <StatRow label="Events Published" value={formatNumber(health.eventsPublished)} />
      <StatRow
        label="Engine Health"
        value={<Badge tone={sessionStateTone(health.currentState)}>{health.currentState}</Badge>}
      />
    </Panel>
  )
}
