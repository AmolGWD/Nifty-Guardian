import type { ReactNode } from 'react'
import styles from './Panel.module.css'

export interface PanelProps {
  title: string
  status?: ReactNode
  children: ReactNode
  className?: string
}

/** The one bordered-card shell every domain panel (Runtime/Market/Trading/...) renders inside. */
export function Panel({ title, status, children, className }: PanelProps) {
  return (
    <section className={className ? `${styles.panel} ${className}` : styles.panel}>
      <header className={styles.header}>
        <h2 className={styles.title}>{title}</h2>
        {status}
      </header>
      <div className={styles.body}>{children}</div>
    </section>
  )
}
