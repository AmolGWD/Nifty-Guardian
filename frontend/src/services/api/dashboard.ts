import type { ApiClientConfig } from './client'
import { apiRequest } from './client'
import type { WireDashboardSnapshot } from './wireTypes'

export function getDashboardSnapshot(config: ApiClientConfig): Promise<WireDashboardSnapshot> {
  return apiRequest<WireDashboardSnapshot>('/api/dashboard', config)
}
