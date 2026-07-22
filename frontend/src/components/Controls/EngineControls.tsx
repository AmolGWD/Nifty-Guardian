import { Panel } from '../Common'
import { useEngineControls } from '../../hooks'
import styles from './EngineControls.module.css'

/**
 * Start/Pause/Resume/Stop/Replay/Reset. Every button is a direct,
 * unconditional call into the service via `useEngineControls()` - no
 * business logic here. Enablement mirrors the backend's own
 * `SESSION_STATE_TRANSITIONS` table (app.runtime.session_controller,
 * frozen) purely as a UI affordance - disabling a button the current
 * session state doesn't allow, not a re-implementation of the state
 * machine itself (the service/backend remains the sole authority; a
 * disabled button here is advisory, not enforcement).
 */
export function EngineControls() {
  const { sessionState, start, pause, resume, stop, replay, reset } = useEngineControls()

  const canStart = sessionState === 'NotStarted'
  const canPause = sessionState === 'Running'
  const canResume = sessionState === 'Paused'
  const canStop = sessionState === 'Running' || sessionState === 'Paused'
  const canReplay = sessionState === 'Stopped' || sessionState === 'Ended'
  const canReset = sessionState !== 'NotStarted'

  return (
    <Panel title="Engine Controls">
      <div className={styles.grid}>
        <button className={styles.button} disabled={!canStart} onClick={start}>
          Start
        </button>
        <button className={styles.button} disabled={!canPause} onClick={pause}>
          Pause
        </button>
        <button className={styles.button} disabled={!canResume} onClick={resume}>
          Resume
        </button>
        <button className={styles.button} disabled={!canStop} onClick={stop}>
          Stop
        </button>
        <button className={styles.button} disabled={!canReplay} onClick={replay}>
          Replay
        </button>
        <button className={styles.button} disabled={!canReset} onClick={reset}>
          Reset
        </button>
      </div>
    </Panel>
  )
}
