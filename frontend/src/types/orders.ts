import type { StrategyDirection } from './trading'

/**
 * Mirrors app.paper_trading.models.Order/OrderStatus (backend, frozen).
 * ORDER_STATUS_TRANSITIONS is the backend's enforced source of truth -
 * this dashboard only ever displays whatever status the backend sent,
 * it never computes or validates a transition itself.
 */
export type OrderStatus =
  'New' | 'Validated' | 'Submitted' | 'PartiallyFilled' | 'Filled' | 'Cancelled' | 'Rejected'

export interface Order {
  orderId: string
  strategyName: string
  direction: StrategyDirection
  requestedPrice: number
  requestedQuantity: number
  filledQuantity: number
  averageFillPrice: number | null
  stopLoss: number
  target: number
  status: OrderStatus
  rejectionReason: string | null
  createdAt: string
  updatedAt: string
}
