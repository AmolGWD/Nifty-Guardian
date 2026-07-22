import type { ApiClientConfig } from './client'
import { apiRequest } from './client'
import type { WireHealthSnapshot, WireRuntimeState, WireRuntimeStats } from './wireTypes'

export interface ReplayRequestBody {
  replay_speed: string
  maximum_candles: number | null
}

export function getRuntimeHealth(config: ApiClientConfig): Promise<WireHealthSnapshot> {
  return apiRequest<WireHealthSnapshot>('/api/runtime/health', config)
}

export function getRuntimeState(config: ApiClientConfig): Promise<WireRuntimeState> {
  return apiRequest<WireRuntimeState>('/api/runtime/state', config)
}

export function postRuntimeStart(config: ApiClientConfig): Promise<WireRuntimeStats> {
  return apiRequest<WireRuntimeStats>('/api/runtime/start', config, { method: 'POST' })
}

export function postRuntimePause(config: ApiClientConfig): Promise<WireRuntimeStats> {
  return apiRequest<WireRuntimeStats>('/api/runtime/pause', config, { method: 'POST' })
}

export function postRuntimeResume(config: ApiClientConfig): Promise<WireRuntimeStats> {
  return apiRequest<WireRuntimeStats>('/api/runtime/resume', config, { method: 'POST' })
}

export function postRuntimeStop(config: ApiClientConfig): Promise<WireRuntimeStats> {
  return apiRequest<WireRuntimeStats>('/api/runtime/stop', config, { method: 'POST' })
}

export function postRuntimeReplay(
  config: ApiClientConfig,
  body: ReplayRequestBody,
): Promise<WireRuntimeStats> {
  return apiRequest<WireRuntimeStats>('/api/runtime/replay', config, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
