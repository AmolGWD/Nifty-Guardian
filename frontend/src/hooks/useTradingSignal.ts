import { useDashboardStore } from './useDashboardStore'
import type { RiskDecision, StrategySignal, TradeRecommendation } from '../types'

export interface TradingSignalData {
  latestSignal: StrategySignal | null
  latestRiskDecision: RiskDecision | null
  latestRecommendation: TradeRecommendation | null
}

export function useTradingSignal(): TradingSignalData {
  const latestSignal = useDashboardStore((state) => state.snapshot.latestSignal)
  const latestRiskDecision = useDashboardStore((state) => state.snapshot.latestRiskDecision)
  const latestRecommendation = useDashboardStore((state) => state.snapshot.latestRecommendation)
  return { latestSignal, latestRiskDecision, latestRecommendation }
}
