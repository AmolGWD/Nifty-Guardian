import type {
  Candle,
  HealthSnapshot,
  JournalEntry,
  MarketContext,
  Order,
  PerformanceSnapshot,
  Portfolio,
  Position,
  ReplaySpeed,
  RiskDecision,
  StrategySignal,
  TradeRecommendation,
} from '../types'

/**
 * The shape of scripts/dashboard_mock_data.json - one entry per
 * candle a replay would process. `orders`/`positions`/`portfolio`/
 * `performance`/`health` are full, cumulative snapshots as of this
 * tick (matching how the real backend's managers always hand back a
 * fresh view, never a delta); `newJournalEntries` is the one
 * append-only exception, since a journal is inherently a growing log.
 */
export interface MockTick {
  candle: Candle
  marketContext: MarketContext
  signal: StrategySignal | null
  riskDecision: RiskDecision | null
  recommendation: TradeRecommendation | null
  orders: Order[]
  positions: Position[]
  portfolio: Portfolio
  performance: PerformanceSnapshot
  health: HealthSnapshot
  newJournalEntries: JournalEntry[]
}

export interface MockDataset {
  totalCandles: number
  warmupCandles: number
  initialCapital: number
  replaySpeed: ReplaySpeed
  randomSeed: number
  ticks: MockTick[]
}
