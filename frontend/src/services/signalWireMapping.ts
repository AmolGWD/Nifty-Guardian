import type {
  WireDailyReport,
  WireDummyTrade,
  WireGuardianScore,
  WireSignalPerformance,
  WireSignalState,
} from './api/signalsWireTypes'
import type {
  DailyReport,
  DummyTrade,
  GuardianScore,
  SignalEngineState,
  SignalPerformance,
} from '../types'

function mapGuardianScore(wire: WireGuardianScore): GuardianScore {
  return {
    score: wire.score,
    strength: wire.strength as GuardianScore['strength'],
    rewardRiskRatio: wire.reward_risk_ratio,
    reasons: wire.reasons,
  }
}

export function mapDummyTrade(wire: WireDummyTrade): DummyTrade {
  return {
    tradeId: wire.trade_id,
    strategyName: wire.strategy_name,
    direction: wire.direction as DummyTrade['direction'],
    guardianScore: mapGuardianScore(wire.guardian_score),
    entryPrice: wire.entry_price,
    stopLoss: wire.stop_loss,
    target: wire.target,
    quantity: wire.quantity,
    openedAt: wire.opened_at,
    status: wire.status as DummyTrade['status'],
    exitPrice: wire.exit_price,
    closedAt: wire.closed_at,
    pnl: wire.pnl,
    rMultiple: wire.r_multiple,
    durationSeconds: wire.duration_seconds,
    exitReason: wire.exit_reason as DummyTrade['exitReason'],
  }
}

export function mapSignalState(wire: WireSignalState): SignalEngineState {
  return {
    marketStatus: wire.market_status as SignalEngineState['marketStatus'],
    marketBias: wire.market_bias as SignalEngineState['marketBias'],
    latestSignalType: wire.latest_signal_type as SignalEngineState['latestSignalType'],
    latestGuardianScore: wire.latest_guardian_score
      ? mapGuardianScore(wire.latest_guardian_score)
      : null,
    latestExplanation: wire.latest_explanation,
    latestSignalAt: wire.latest_signal_at,
    latestEntryPrice: wire.latest_entry_price,
    latestStopLoss: wire.latest_stop_loss,
    latestTarget: wire.latest_target,
    signalsSentToday: wire.signals_sent_today,
    telegramStatus: wire.telegram_status as SignalEngineState['telegramStatus'],
  }
}

export function mapSignalPerformance(wire: WireSignalPerformance): SignalPerformance {
  return {
    openTrades: wire.open_trades.map(mapDummyTrade),
    closedTrades: wire.closed_trades.map(mapDummyTrade),
    winRate: wire.win_rate,
    todayPnl: wire.today_pnl,
    weeklyPnl: wire.weekly_pnl,
    monthlyPnl: wire.monthly_pnl,
  }
}

export function mapDailyReport(wire: WireDailyReport): DailyReport {
  return {
    reportDate: wire.report_date,
    totalSignals: wire.total_signals,
    buyCeCount: wire.buy_ce_count,
    buyPeCount: wire.buy_pe_count,
    winningTrades: wire.winning_trades,
    losingTrades: wire.losing_trades,
    winRate: wire.win_rate,
    netPoints: wire.net_points,
    averagePnl: wire.average_pnl,
    averageRewardRiskRatio: wire.average_reward_risk_ratio,
    bestTrade: wire.best_trade ? mapDummyTrade(wire.best_trade) : null,
    worstTrade: wire.worst_trade ? mapDummyTrade(wire.worst_trade) : null,
    highestGuardianScore: wire.highest_guardian_score,
    averageHoldTimeSeconds: wire.average_hold_time_seconds,
    marketBias: wire.market_bias as DailyReport['marketBias'],
    guardianStatus: wire.guardian_status,
  }
}
