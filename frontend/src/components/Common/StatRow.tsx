import type { ReactNode } from 'react'
import styles from './StatRow.module.css'

export interface StatRowProps {
  label: string
  value: ReactNode
  tone?: 'positive' | 'negative' | 'neutral'
}

const TONE_CLASS = {
  positive: styles.positive,
  negative: styles.negative,
  neutral: '',
} as const

/** A label/value line - the basic unit every stat-listing panel (Runtime/Market/Portfolio/Health) is built from. */
export function StatRow({ label, value, tone = 'neutral' }: StatRowProps) {
  return (
    <div className={styles.row}>
      <span className={styles.label}>{label}</span>
      <span className={`${styles.value} ${TONE_CLASS[tone]}`}>{value}</span>
    </div>
  )
}
