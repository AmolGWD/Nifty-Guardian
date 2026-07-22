import { Badge, sessionStateTone } from '../Common'
import { useRuntimeStats } from '../../hooks'
import styles from './Header.module.css'

/** App title bar - session state at a glance, nothing else. Every other stat lives in its own panel. */
export function Header() {
  const runtime = useRuntimeStats()

  return (
    <header className={styles.header}>
      <div className={styles.titleGroup}>
        <span className={styles.title}>NIFTY GUARDIAN</span>
        <span className={styles.tagline}>Paper Trading Operations Console</span>
      </div>
      <div className={styles.statusGroup}>
        <span className={styles.statusLabel}>SESSION</span>
        <Badge tone={sessionStateTone(runtime.sessionState)}>{runtime.sessionState}</Badge>
      </div>
    </header>
  )
}
