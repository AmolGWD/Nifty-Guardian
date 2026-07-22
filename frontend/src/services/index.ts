import { MockDashboardService } from './mockDashboardService'
import type { DashboardService } from './dashboardService'

/**
 * The one service instance every hook/store/component in this
 * dashboard imports. Swapping to a real backend later means replacing
 * this single assignment with a `RestDashboardService`/
 * `WebSocketDashboardService` that implements the same
 * `DashboardService` interface - see docs/DASHBOARD_GUIDE.md.
 */
export const dashboardService: DashboardService = new MockDashboardService()

export type { DashboardService } from './dashboardService'
export { MockDashboardService } from './mockDashboardService'
