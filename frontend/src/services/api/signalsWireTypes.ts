/**
 * snake_case wire shapes for /api/signals/* - mirrors
 * backend/app/api/signals/signals_models.py exactly. Kept in its own
 * file rather than added to wireTypes.ts to avoid any edit to the
 * existing Backend Connectivity surface (Phase 22, frozen).
 */

export interface WireGuardianScore {
  score: number
  strength: string
  reward_risk_ratio: number
  reasons: string[]
}

export interface WireDummyTrade {
  trade_id: string
  strategy_name: string
  direction: string
  guardian_score: WireGuardianScore
  entry_price: number
  stop_loss: number
  target: number
  quantity: number
  opened_at: string
  status: string
  exit_price: number | null
  closed_at: string | null
  pnl: number | null
  r_multiple: number | null
  duration_seconds: number | null
  exit_reason: string | null
}

export interface WireSignalState {
  market_bias: string
  latest_signal_type: string | null
  latest_guardian_score: WireGuardianScore | null
  latest_explanation: string | null
  latest_signal_at: string | null
  signals_sent_today: number
}

export interface WireSignalPerformance {
  open_trades: WireDummyTrade[]
  closed_trades: WireDummyTrade[]
  win_rate: number
  today_pnl: number
  weekly_pnl: number
  monthly_pnl: number
}

export interface WireDailyReport {
  report_date: string
  total_signals: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  net_points: number
  average_reward_risk_ratio: number
  best_trade: WireDummyTrade | null
  worst_trade: WireDummyTrade | null
}

export interface WireEngineStatus {
  running: boolean
  live_session_state: string | null
}
