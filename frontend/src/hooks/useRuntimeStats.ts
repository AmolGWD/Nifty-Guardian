import { useDashboardStore } from './useDashboardStore'
import type { RuntimeStats } from '../types'

export function useRuntimeStats(): RuntimeStats {
  return useDashboardStore((state) => state.snapshot.runtime)
}
