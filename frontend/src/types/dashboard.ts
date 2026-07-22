import type { Candle, MarketContext } from './market'
import type { JournalEntry } from './journal'
import type { Order } from './orders'
import type { Portfolio } from './portfolio'
import type { Position } from './positions'
import type { RuntimeStats } from './runtime'
import type { RiskDecision, StrategySignal, TradeRecommendation } from './trading'
import type { HealthSnapshot, PerformanceSnapshot } from './health'

/**
 * The single composed snapshot a `DashboardService` emits on every
 * tick - the shape every panel reads from via the store. One snapshot
 * per tick keeps the store update atomic (every panel sees the same
 * point in time), the same reason `PortfolioManager.snapshot()`
 * (backend) is a single fresh view rather than several independently-
 * timestamped reads.
 */
export interface DashboardSnapshot {
  runtime: RuntimeStats
  currentCandle: Candle | null
  marketContext: MarketContext | null
  latestSignal: StrategySignal | null
  latestRiskDecision: RiskDecision | null
  latestRecommendation: TradeRecommendation | null
  orders: Order[]
  positions: Position[]
  portfolio: Portfolio
  journal: JournalEntry[]
  health: HealthSnapshot
  performance: PerformanceSnapshot
}
