import { loadDashboardConfig } from './config'
import { MockDashboardService } from './mockDashboardService'
import { RestDashboardService } from './restDashboardService'
import type { DashboardService } from './dashboardService'

/**
 * The one service instance every hook/store/component in this
 * dashboard imports. Which concrete implementation backs it is a pure
 * configuration choice (`VITE_DASHBOARD_SERVICE=mock|rest`, default
 * `mock`) - nothing else in this codebase branches on it. See
 * docs/DASHBOARD_GUIDE.md/docs/API_GUIDE.md.
 */
const dashboardConfig = loadDashboardConfig()

export const dashboardService: DashboardService =
  dashboardConfig.serviceMode === 'rest'
    ? new RestDashboardService(dashboardConfig)
    : new MockDashboardService()

export type { DashboardService } from './dashboardService'
export { loadDashboardConfig } from './config'
export type { DashboardConfig, DashboardServiceMode } from './config'
export { MockDashboardService } from './mockDashboardService'
export { RestDashboardService } from './restDashboardService'
