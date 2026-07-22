import { useDashboardStore } from './useDashboardStore'
import type { Position } from '../types'

export function usePositions(): Position[] {
  return useDashboardStore((state) => state.snapshot.positions)
}
