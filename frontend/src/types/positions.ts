import type { StrategyDirection } from './trading'

/** Mirrors app.paper_trading.models.Position/PositionStatus (backend, frozen). */
export type PositionStatus = 'Open' | 'PartiallyExited' | 'Closed'

export interface Position {
  positionId: string
  strategyName: string
  direction: StrategyDirection
  averageEntryPrice: number
  quantity: number
  initialQuantity: number
  realizedPnl: number
  unrealizedPnl: number
  status: PositionStatus
  openedAt: string
  closedAt: string | null
}
