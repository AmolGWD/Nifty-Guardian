/** Shared display formatting - no calculation, only presentation of values the backend already computed. */

export function formatCurrency(value: number): string {
  return value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`
}

export function formatNumber(value: number): string {
  return value.toLocaleString('en-IN')
}

export function formatSeconds(value: number): string {
  return `${value.toFixed(2)}s`
}

export function formatTime(isoTimestamp: string): string {
  const date = new Date(isoTimestamp)
  return Number.isNaN(date.getTime())
    ? isoTimestamp
    : date.toLocaleTimeString('en-IN', { hour12: false })
}

export function formatDateTime(isoTimestamp: string): string {
  const date = new Date(isoTimestamp)
  return Number.isNaN(date.getTime())
    ? isoTimestamp
    : date.toLocaleString('en-IN', { hour12: false })
}
