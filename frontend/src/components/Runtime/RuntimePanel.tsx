import { Badge, Panel, StatRow, formatNumber, formatSeconds, sessionStateTone } from '../Common'
import { useRuntimeStats } from '../../hooks'

/**
 * Engine State, Replay Speed, Processed Candles, Events Published,
 * Runtime Uptime, Session State - the CTO brief lists "Engine State"
 * and "Session State" as separate display items; the backend
 * (app.runtime.session_controller.SessionState) exposes exactly one
 * underlying value for both, so both rows show it - not two different
 * pieces of state this dashboard invents.
 */
export function RuntimePanel() {
  const runtime = useRuntimeStats()
  const stateBadge = (
    <Badge tone={sessionStateTone(runtime.sessionState)}>{runtime.sessionState}</Badge>
  )

  return (
    <Panel title="Runtime">
      <StatRow label="Engine State" value={stateBadge} />
      <StatRow label="Replay Speed" value={runtime.replaySpeed} />
      <StatRow
        label="Processed Candles"
        value={`${formatNumber(runtime.processedCandles)} / ${formatNumber(runtime.totalCandles)}`}
      />
      <StatRow label="Events Published" value={formatNumber(runtime.eventsPublished)} />
      <StatRow label="Orders Generated" value={formatNumber(runtime.ordersGenerated)} />
      <StatRow label="Runtime Uptime" value={formatSeconds(runtime.uptimeSeconds)} />
      <StatRow label="Session State" value={stateBadge} />
    </Panel>
  )
}
