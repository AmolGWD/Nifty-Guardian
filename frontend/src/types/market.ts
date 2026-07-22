/** Mirrors app.market_data.schemas.Candle (backend, frozen). */
export interface Candle {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

/** Mirrors app.trading.context.models.MarketContext (backend, frozen). */
export type TrendContext = 'BullishTrend' | 'BearishTrend' | 'SidewaysTrend'
export type MomentumContext = 'StrongMomentum' | 'WeakMomentum'
export type VolatilityContext = 'HighVolatility' | 'LowVolatility'
export type VolumeStrengthContext = 'StrongVolume' | 'WeakVolume' | 'AverageVolume'
export type Bias = 'BullishBias' | 'BearishBias' | 'NeutralBias'
export type OverallMarketState =
  'StrongBullish' | 'StrongBearish' | 'RangeBound' | 'VolatileRange' | 'Mixed'
export type MarketSessionStatus = 'PRE_MARKET' | 'OPEN' | 'CLOSED'

export interface MarketContext {
  asOf: string
  trend: TrendContext
  momentum: MomentumContext
  volatility: VolatilityContext
  volumeStrength: VolumeStrengthContext
  marketBias: Bias
  optionChainBias: Bias
  sessionState: MarketSessionStatus
  overallState: OverallMarketState
}
