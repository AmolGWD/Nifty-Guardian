import type { BadgeTone } from './Badge'
import type { SessionState } from '../../types'
import type { OrderStatus } from '../../types'
import type { PositionStatus } from '../../types'
import type { JournalEntryType } from '../../types'

export function sessionStateTone(state: SessionState): BadgeTone {
  switch (state) {
    case 'Running':
      return 'positive'
    case 'Paused':
      return 'warning'
    case 'Stopped':
    case 'Ended':
      return 'neutral'
    case 'NotStarted':
      return 'neutral'
  }
}

export function orderStatusTone(status: OrderStatus): BadgeTone {
  switch (status) {
    case 'Filled':
      return 'positive'
    case 'Rejected':
    case 'Cancelled':
      return 'negative'
    case 'PartiallyFilled':
      return 'warning'
    case 'New':
    case 'Validated':
    case 'Submitted':
      return 'accent'
  }
}

export function positionStatusTone(status: PositionStatus): BadgeTone {
  switch (status) {
    case 'Open':
      return 'accent'
    case 'PartiallyExited':
      return 'warning'
    case 'Closed':
      return 'neutral'
  }
}

export function journalEntryTone(entryType: JournalEntryType): BadgeTone {
  return entryType === 'Error' ? 'negative' : 'neutral'
}

export type PnlTone = 'positive' | 'negative' | 'neutral'

export function pnlTone(value: number): PnlTone {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const PNL_COLOR: Record<PnlTone, string> = {
  positive: 'var(--color-positive)',
  negative: 'var(--color-negative)',
  neutral: 'var(--color-text)',
}

export function pnlColor(value: number): string {
  return PNL_COLOR[pnlTone(value)]
}
