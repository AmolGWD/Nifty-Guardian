import { create } from 'zustand'
import { loadDashboardConfig } from '../services'
import { SignalEngineService } from '../services/signalEngineService'
import type { SignalEngineSnapshot } from '../services/signalEngineService'

interface SignalEngineStoreState {
  snapshot: SignalEngineSnapshot
  start: () => void
  stop: () => void
}

/**
 * The single store every Signal Engine panel reads from - reuses the
 * same `apiBaseUrl`/`apiTimeoutMs`/`pollingIntervalMs` config the
 * Dashboard's own REST connectivity already loads (`loadDashboardConfig()`,
 * Phase 22, frozen, read-only here), rather than inventing a second
 * config-loading path for what is the same backend process.
 */
const config = loadDashboardConfig()
const signalEngineService = new SignalEngineService({
  apiBaseUrl: config.apiBaseUrl,
  apiTimeoutMs: config.apiTimeoutMs,
  pollingIntervalMs: config.pollingIntervalMs,
})

export const useSignalEngineStore = create<SignalEngineStoreState>((set) => {
  signalEngineService.subscribe((snapshot) => {
    set({ snapshot })
  })

  return {
    snapshot: signalEngineService.getSnapshot(),
    start: () => signalEngineService.start(),
    stop: () => signalEngineService.stop(),
  }
})
