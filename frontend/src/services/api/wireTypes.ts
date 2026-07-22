/**
 * The exact snake_case shapes backend/app/api/dashboard/*_models.py
 * serializes - deliberately kept separate from `types/*.ts`'s
 * camelCase domain types. `dashboard.ts`/`runtime.ts` return these
 * as-is; `restDashboardService.ts` owns mapping them into the
 * camelCase `DashboardSnapshot` shape the (frozen) store/components
 * consume - see docs/DASHBOARD_GUIDE.md's "Backend integration plan",
 * written before this phase existed specifically to anticipate this
 * split.
 */

export interface WireCandle {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface WireMarketContext {
  as_of: string
  trend: string
  momentum: string
  volatility: string
  volume_strength: string
  market_bias: string
  option_chain_bias: string
  session_state: string
  overall_state: string
}

export interface WireStrategySignal {
  strategy_name: string
  valid: boolean
  direction: string
  strength: string
  reasons: string[]
  warnings: string[]
}

export interface WireRiskDecision {
  risk_ok: boolean
  position_size: number
  stop_loss: number
  target: number
  reward_risk_ratio: number
  capital_required: number
  rejection_reasons: string[]
}

export interface WireTradeRecommendation {
  recommended: boolean
  direction: string
  selected_strategy: string | null
  recommendation_strength: string | null
  reasons: string[]
  warnings: string[]
}

export interface WireOrder {
  order_id: string
  strategy_name: string
  direction: string
  requested_price: number
  requested_quantity: number
  filled_quantity: number
  average_fill_price: number | null
  stop_loss: number
  target: number
  status: string
  rejection_reason: string | null
  created_at: string
  updated_at: string
}

export interface WirePosition {
  position_id: string
  strategy_name: string
  direction: string
  average_entry_price: number
  quantity: number
  initial_quantity: number
  realized_pnl: number
  unrealized_pnl: number
  status: string
  opened_at: string
  closed_at: string | null
}

export interface WirePortfolio {
  as_of: string
  cash: number
  available_margin: number
  open_position_ids: string[]
  closed_position_ids: string[]
  daily_pnl: number
  total_equity: number
  peak_equity: number
  drawdown: number
  drawdown_percent: number
}

export interface WireJournalEntry {
  entry_id: string
  entry_type: string
  timestamp: string
  source_event_id: string
  description: string
}

export interface WireHealthSnapshot {
  processed_candles: number
  average_processing_latency_seconds: number | null
  uptime_seconds: number
  events_published: number
  orders_generated: number
  current_state: string
}

export interface WirePerformanceSnapshot {
  orders_submitted: number
  orders_filled: number
  orders_rejected: number
  orders_cancelled: number
  fill_ratio_percent: number
  daily_return_percent: number
  max_drawdown: number
  average_execution_latency_seconds: number | null
  win_rate_percent: number
}

export interface WireRuntimeStats {
  session_state: string
  replay_speed: string
  processed_candles: number
  total_candles: number
  events_published: number
  orders_generated: number
  uptime_seconds: number
}

export interface WireDashboardSnapshot {
  runtime: WireRuntimeStats
  current_candle: WireCandle | null
  market_context: WireMarketContext | null
  latest_signal: WireStrategySignal | null
  latest_risk_decision: WireRiskDecision | null
  latest_recommendation: WireTradeRecommendation | null
  orders: WireOrder[]
  positions: WirePosition[]
  portfolio: WirePortfolio
  journal: WireJournalEntry[]
  health: WireHealthSnapshot
  performance: WirePerformanceSnapshot
}

export interface WireRuntimeState {
  state: string
}
