import type { ReactNode } from 'react'
import styles from './Badge.module.css'

export type BadgeTone = 'neutral' | 'positive' | 'negative' | 'warning' | 'accent'

export interface BadgeProps {
  children: ReactNode
  tone?: BadgeTone
}

/** A small status pill - used for order/position status, session state, journal entry type. */
export function Badge({ children, tone = 'neutral' }: BadgeProps) {
  return <span className={`${styles.badge} ${styles[tone]}`}>{children}</span>
}
