import { useDashboardStore } from './useDashboardStore'
import type { HealthSnapshot, PerformanceSnapshot } from '../types'

export interface HealthData {
  health: HealthSnapshot
  performance: PerformanceSnapshot
}

export function useHealth(): HealthData {
  const health = useDashboardStore((state) => state.snapshot.health)
  const performance = useDashboardStore((state) => state.snapshot.performance)
  return { health, performance }
}
