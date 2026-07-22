import { Badge, EmptyState, Panel, formatTime, journalEntryTone } from '../Common'
import { useJournal } from '../../hooks'
import styles from './JournalPanel.module.css'

/** Scrollable log: Signals, Orders, Events, Errors, Runtime Messages - newest first. */
export function JournalPanel() {
  const journal = useJournal()

  if (journal.length === 0) {
    return (
      <Panel title="Journal">
        <EmptyState message="No journal entries yet." />
      </Panel>
    )
  }

  // Newest first: reverse in JS rather than via `flex-direction:
  // column-reverse` - a reversed flex container with `overflow-y: auto`
  // scrolls to reveal the DOM-first (oldest) child when content
  // overflows, not the last, which showed stale entries at the top.
  const newestFirst = [...journal].reverse()

  return (
    <Panel title="Journal">
      <div className={styles.list}>
        {newestFirst.map((entry) => (
          <div key={entry.entryId} className={styles.entry}>
            <span className={styles.time}>{formatTime(entry.timestamp)}</span>
            <Badge tone={journalEntryTone(entry.entryType)}>{entry.entryType}</Badge>
            <span className={styles.description}>{entry.description}</span>
          </div>
        ))}
      </div>
    </Panel>
  )
}
