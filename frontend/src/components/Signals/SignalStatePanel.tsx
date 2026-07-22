import { Badge, EmptyState, Panel, StatRow, formatDateTime } from '../Common'
import { useSignalEngine } from '../../hooks'
import styles from './SignalStatePanel.module.css'

const BIAS_TONE = { Long: 'positive', Short: 'negative', None: 'neutral' } as const

/**
 * Current Market Bias, Current Signal, Guardian Score, Signal
 * Confidence, and Reasons - plus Start/Stop for the Signal Engine
 * session itself. "Confidence" is `StrategyStrength`, reused directly
 * from the backend (never a number this dashboard invents); "Guardian
 * Score" is the new, numeric 0-100 aggregate `app.signals.
 * confidence_engine` computes - the two are shown side by side, never
 * conflated.
 */
export function SignalStatePanel() {
  const { running, state, start, stop } = useSignalEngine()

  return (
    <Panel
      title="Signal Engine"
      status={
        <Badge tone={running ? 'positive' : 'neutral'}>{running ? 'Running' : 'Stopped'}</Badge>
      }
    >
      <div className={styles.controls}>
        <button className={styles.button} disabled={running} onClick={start}>
          Start Signals
        </button>
        <button className={styles.button} disabled={!running} onClick={stop}>
          Stop Signals
        </button>
      </div>

      <StatRow
        label="Market Bias"
        value={<Badge tone={BIAS_TONE[state.marketBias]}>{state.marketBias}</Badge>}
      />
      <StatRow label="Signal" value={state.latestSignalType ?? '-'} />
      {state.latestGuardianScore ? (
        <>
          <StatRow label="Confidence" value={state.latestGuardianScore.strength} />
          <StatRow label="Guardian Score" value={state.latestGuardianScore.score.toFixed(1)} />
          <StatRow label="RR" value={state.latestGuardianScore.rewardRiskRatio.toFixed(2)} />
        </>
      ) : (
        <EmptyState message="No signal yet." />
      )}
      {state.latestSignalAt && (
        <StatRow label="Last Signal At" value={formatDateTime(state.latestSignalAt)} />
      )}
      <StatRow label="Signals Sent Today" value={state.signalsSentToday} />

      {state.latestGuardianScore && state.latestGuardianScore.reasons.length > 0 && (
        <ul className={styles.reasons}>
          {state.latestGuardianScore.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
    </Panel>
  )
}
