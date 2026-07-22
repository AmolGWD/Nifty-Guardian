import { useDashboardStore } from './useDashboardStore'
import type { JournalEntry } from '../types'

export function useJournal(): JournalEntry[] {
  return useDashboardStore((state) => state.snapshot.journal)
}
