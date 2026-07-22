/**
 * Mirrors app.signals.models (backend, new this phase) - the Guardian
 * Score, dummy (paper) trades, and daily performance reporting the
 * Signal Engine produces. "Confidence" here is `strength`, reused
 * directly from `StrategyStrength` (see types/trading.ts) - the
 * Guardian Score is a distinct, new, numeric field, never a
 * replacement for it.
 */
import type { StrategyDirection, StrategyStrength } from './trading'

export type SignalType = 'BuyCE' | 'BuyPE' | 'TargetHit' | 'StoplossHit' | 'NoTrade'
export type DummyTradeStatus = 'Open' | 'Closed'
export type ExitReason = 'Target' | 'StopLoss' | 'EndOfDay' | 'Unknown'

export interface GuardianScore {
  score: number
  strength: StrategyStrength
  rewardRiskRatio: number
  reasons: string[]
}

export interface DummyTrade {
  tradeId: string
  strategyName: string
  direction: StrategyDirection
  guardianScore: GuardianScore
  entryPrice: number
  stopLoss: number
  target: number
  quantity: number
  openedAt: string
  status: DummyTradeStatus
  exitPrice: number | null
  closedAt: string | null
  pnl: number | null
  rMultiple: number | null
  durationSeconds: number | null
  exitReason: ExitReason | null
}

export interface SignalEngineState {
  marketBias: StrategyDirection
  latestSignalType: SignalType | null
  latestGuardianScore: GuardianScore | null
  latestExplanation: string | null
  latestSignalAt: string | null
  signalsSentToday: number
}

export interface SignalPerformance {
  openTrades: DummyTrade[]
  closedTrades: DummyTrade[]
  winRate: number
  todayPnl: number
  weeklyPnl: number
  monthlyPnl: number
}

export interface DailyReport {
  reportDate: string
  totalSignals: number
  winningTrades: number
  losingTrades: number
  winRate: number
  netPoints: number
  averageRewardRiskRatio: number
  bestTrade: DummyTrade | null
  worstTrade: DummyTrade | null
}

export interface SignalEngineStatus {
  running: boolean
  liveSessionState: string | null
}
