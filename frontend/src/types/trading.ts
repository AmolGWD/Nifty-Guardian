/**
 * Mirrors app.trading.strategy.models.StrategyEvaluation,
 * app.trading.risk.models.RiskAssessment, and
 * app.trading.decision.models.TradeRecommendation (backend, frozen).
 * "Confidence" in this dashboard is always one of these backend
 * fields - never a number this dashboard invents.
 */
export type StrategyDirection = 'Long' | 'Short' | 'None'
export type StrategyStrength = 'Strong' | 'Moderate' | 'Weak'

export interface StrategySignal {
  strategyName: string
  valid: boolean
  direction: StrategyDirection
  strength: StrategyStrength
  reasons: string[]
  warnings: string[]
}

export type RiskRejectionReason =
  | 'DailyLossLimitExceeded'
  | 'MaxTradesPerDayReached'
  | 'CapitalExposureExceeded'
  | 'MaxConcurrentPositionsReached'
  | 'PositionSizeTooSmall'

export interface RiskDecision {
  riskOk: boolean
  positionSize: number
  stopLoss: number
  target: number
  rewardRiskRatio: number
  capitalRequired: number
  rejectionReasons: RiskRejectionReason[]
}

export type RecommendationStrength = 'Strong' | 'Moderate' | 'Weak'

export interface TradeRecommendation {
  recommended: boolean
  direction: StrategyDirection
  selectedStrategy: string | null
  recommendationStrength: RecommendationStrength | null
  reasons: string[]
  warnings: string[]
}
