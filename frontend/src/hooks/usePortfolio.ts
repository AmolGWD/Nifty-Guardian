import { useDashboardStore } from './useDashboardStore'
import type { Portfolio } from '../types'

export function usePortfolio(): Portfolio {
  return useDashboardStore((state) => state.snapshot.portfolio)
}
