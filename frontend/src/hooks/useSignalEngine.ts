import { useSignalEngineStore } from './useSignalEngineStore'
import type { DailyReport, DummyTrade, SignalEngineState, SignalPerformance } from '../types'

export interface SignalEngineData {
  running: boolean
  state: SignalEngineState
  performance: SignalPerformance
  trades: DummyTrade[]
  report: DailyReport
  start: () => void
  stop: () => void
}

export function useSignalEngine(): SignalEngineData {
  const running = useSignalEngineStore((s) => s.snapshot.running)
  const state = useSignalEngineStore((s) => s.snapshot.state)
  const performance = useSignalEngineStore((s) => s.snapshot.performance)
  const trades = useSignalEngineStore((s) => s.snapshot.trades)
  const report = useSignalEngineStore((s) => s.snapshot.report)
  const start = useSignalEngineStore((s) => s.start)
  const stop = useSignalEngineStore((s) => s.stop)
  return { running, state, performance, trades, report, start, stop }
}
