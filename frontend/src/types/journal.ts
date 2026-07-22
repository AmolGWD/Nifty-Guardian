/** Mirrors app.paper_trading.execution_journal.JournalEntry/JournalEntryType (backend, frozen). */
export type JournalEntryType =
  'Signal' | 'Risk' | 'Order' | 'Execution' | 'Position' | 'Portfolio' | 'Error'

export interface JournalEntry {
  entryId: string
  entryType: JournalEntryType
  timestamp: string
  sourceEventId: string
  description: string
}
