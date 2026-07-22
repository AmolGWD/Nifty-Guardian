import { useDashboardStore } from './useDashboardStore'
import type { Order } from '../types'

export function useOrders(): Order[] {
  return useDashboardStore((state) => state.snapshot.orders)
}
