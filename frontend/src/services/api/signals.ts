import type { ApiClientConfig } from './client'
import { apiRequest } from './client'
import type {
  WireDailyReport,
  WireDummyTrade,
  WireEngineStatus,
  WireSignalPerformance,
  WireSignalState,
} from './signalsWireTypes'

export function getSignalState(config: ApiClientConfig): Promise<WireSignalState> {
  return apiRequest<WireSignalState>('/api/signals/state', config)
}

export function getSignalPerformance(config: ApiClientConfig): Promise<WireSignalPerformance> {
  return apiRequest<WireSignalPerformance>('/api/signals/performance', config)
}

export function getSignalTrades(config: ApiClientConfig): Promise<WireDummyTrade[]> {
  return apiRequest<WireDummyTrade[]>('/api/signals/trades', config)
}

export function getSignalReportToday(config: ApiClientConfig): Promise<WireDailyReport> {
  return apiRequest<WireDailyReport>('/api/signals/report/today', config)
}

export function getSignalEngineStatus(config: ApiClientConfig): Promise<WireEngineStatus> {
  return apiRequest<WireEngineStatus>('/api/signals/status', config)
}

export function postSignalEngineStart(config: ApiClientConfig): Promise<WireEngineStatus> {
  return apiRequest<WireEngineStatus>('/api/signals/start', config, { method: 'POST' })
}

export function postSignalEngineStop(config: ApiClientConfig): Promise<WireEngineStatus> {
  return apiRequest<WireEngineStatus>('/api/signals/stop', config, { method: 'POST' })
}
