/**
 * Mirrors app.paper_trading.models.Portfolio (backend, frozen).
 * `drawdown`/`drawdownPercent` are computed backend-side
 * (`max(0, peakEquity - totalEquity)`) - this dashboard never
 * recomputes them, only displays what it's given.
 */
export interface Portfolio {
  asOf: string
  cash: number
  availableMargin: number
  openPositionIds: string[]
  closedPositionIds: string[]
  dailyPnl: number
  totalEquity: number
  peakEquity: number
  drawdown: number
  drawdownPercent: number
}
