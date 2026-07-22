import type { ReplaySpeed } from '../types'

export type DashboardServiceMode = 'mock' | 'rest'

export interface DashboardConfig {
  serviceMode: DashboardServiceMode
  apiBaseUrl: string
  pollingIntervalMs: number
  apiTimeoutMs: number
  defaultReplaySpeed: ReplaySpeed
}

const VALID_REPLAY_SPEEDS: ReplaySpeed[] = ['1x', '2x', '5x', '10x', 'Unlimited']

function parsePositiveInt(value: string | undefined, fallback: number): number {
  if (!value) return fallback
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

function parseReplaySpeed(value: string | undefined, fallback: ReplaySpeed): ReplaySpeed {
  return (VALID_REPLAY_SPEEDS as string[]).includes(value ?? '') ? (value as ReplaySpeed) : fallback
}

/**
 * Every environment variable this phase adds, read once with an
 * explicit, honest default - never a silent throw on a missing/
 * malformed value, since a misconfigured dashboard should still boot
 * (against sensible defaults) rather than fail to render at all.
 */
export function loadDashboardConfig(): DashboardConfig {
  const env = import.meta.env

  const serviceMode: DashboardServiceMode = env.VITE_DASHBOARD_SERVICE === 'rest' ? 'rest' : 'mock'

  return {
    serviceMode,
    apiBaseUrl: env.VITE_API_BASE_URL || 'http://localhost:8000',
    pollingIntervalMs: parsePositiveInt(env.VITE_DASHBOARD_POLLING_INTERVAL_MS, 1000),
    apiTimeoutMs: parsePositiveInt(env.VITE_API_TIMEOUT_MS, 5000),
    defaultReplaySpeed: parseReplaySpeed(env.VITE_DEFAULT_REPLAY_SPEED, '1x'),
  }
}
