/**
 * Maps the backend's exact snake_case wire shapes
 * (services/api/wireTypes.ts) into this dashboard's own camelCase
 * domain types (types/*.ts) - the one place that conversion happens,
 * so RestDashboardService's polling loop stays readable and every
 * mapping decision (a null vs. a default, an enum cast) is in one spot.
 */
import type {
  DashboardSnapshot,
  Candle,
  MarketContext,
  StrategySignal,
  RiskDecision,
  TradeRecommendation,
  Order,
  Position,
  Portfolio,
  JournalEntry,
  HealthSnapshot,
  PerformanceSnapshot,
  RuntimeStats,
} from '../types'
import type {
  WireCandle,
  WireDashboardSnapshot,
  WireHealthSnapshot,
  WireJournalEntry,
  WireMarketContext,
  WireOrder,
  WirePerformanceSnapshot,
  WirePortfolio,
  WirePosition,
  WireRiskDecision,
  WireRuntimeStats,
  WireStrategySignal,
  WireTradeRecommendation,
} from './api/wireTypes'

function mapCandle(wire: WireCandle): Candle {
  return {
    timestamp: wire.timestamp,
    open: wire.open,
    high: wire.high,
    low: wire.low,
    close: wire.close,
    volume: wire.volume,
  }
}

function mapMarketContext(wire: WireMarketContext): MarketContext {
  return {
    asOf: wire.as_of,
    trend: wire.trend as MarketContext['trend'],
    momentum: wire.momentum as MarketContext['momentum'],
    volatility: wire.volatility as MarketContext['volatility'],
    volumeStrength: wire.volume_strength as MarketContext['volumeStrength'],
    marketBias: wire.market_bias as MarketContext['marketBias'],
    optionChainBias: wire.option_chain_bias as MarketContext['optionChainBias'],
    sessionState: wire.session_state as MarketContext['sessionState'],
    overallState: wire.overall_state as MarketContext['overallState'],
  }
}

function mapSignal(wire: WireStrategySignal): StrategySignal {
  return {
    strategyName: wire.strategy_name,
    valid: wire.valid,
    direction: wire.direction as StrategySignal['direction'],
    strength: wire.strength as StrategySignal['strength'],
    reasons: wire.reasons,
    warnings: wire.warnings,
  }
}

function mapRiskDecision(wire: WireRiskDecision): RiskDecision {
  return {
    riskOk: wire.risk_ok,
    positionSize: wire.position_size,
    stopLoss: wire.stop_loss,
    target: wire.target,
    rewardRiskRatio: wire.reward_risk_ratio,
    capitalRequired: wire.capital_required,
    rejectionReasons: wire.rejection_reasons as RiskDecision['rejectionReasons'],
  }
}

function mapRecommendation(wire: WireTradeRecommendation): TradeRecommendation {
  return {
    recommended: wire.recommended,
    direction: wire.direction as TradeRecommendation['direction'],
    selectedStrategy: wire.selected_strategy,
    recommendationStrength:
      wire.recommendation_strength as TradeRecommendation['recommendationStrength'],
    reasons: wire.reasons,
    warnings: wire.warnings,
  }
}

function mapOrder(wire: WireOrder): Order {
  return {
    orderId: wire.order_id,
    strategyName: wire.strategy_name,
    direction: wire.direction as Order['direction'],
    requestedPrice: wire.requested_price,
    requestedQuantity: wire.requested_quantity,
    filledQuantity: wire.filled_quantity,
    averageFillPrice: wire.average_fill_price,
    stopLoss: wire.stop_loss,
    target: wire.target,
    status: wire.status as Order['status'],
    rejectionReason: wire.rejection_reason,
    createdAt: wire.created_at,
    updatedAt: wire.updated_at,
  }
}

function mapPosition(wire: WirePosition): Position {
  return {
    positionId: wire.position_id,
    strategyName: wire.strategy_name,
    direction: wire.direction as Position['direction'],
    averageEntryPrice: wire.average_entry_price,
    quantity: wire.quantity,
    initialQuantity: wire.initial_quantity,
    realizedPnl: wire.realized_pnl,
    unrealizedPnl: wire.unrealized_pnl,
    status: wire.status as Position['status'],
    openedAt: wire.opened_at,
    closedAt: wire.closed_at,
  }
}

function mapPortfolio(wire: WirePortfolio): Portfolio {
  return {
    asOf: wire.as_of,
    cash: wire.cash,
    availableMargin: wire.available_margin,
    openPositionIds: wire.open_position_ids,
    closedPositionIds: wire.closed_position_ids,
    dailyPnl: wire.daily_pnl,
    totalEquity: wire.total_equity,
    peakEquity: wire.peak_equity,
    drawdown: wire.drawdown,
    drawdownPercent: wire.drawdown_percent,
  }
}

function mapJournalEntry(wire: WireJournalEntry): JournalEntry {
  return {
    entryId: wire.entry_id,
    entryType: wire.entry_type as JournalEntry['entryType'],
    timestamp: wire.timestamp,
    sourceEventId: wire.source_event_id,
    description: wire.description,
  }
}

function mapHealth(wire: WireHealthSnapshot): HealthSnapshot {
  return {
    processedCandles: wire.processed_candles,
    averageProcessingLatencySeconds: wire.average_processing_latency_seconds,
    uptimeSeconds: wire.uptime_seconds,
    eventsPublished: wire.events_published,
    ordersGenerated: wire.orders_generated,
    currentState: wire.current_state as HealthSnapshot['currentState'],
  }
}

function mapPerformance(wire: WirePerformanceSnapshot): PerformanceSnapshot {
  return {
    ordersSubmitted: wire.orders_submitted,
    ordersFilled: wire.orders_filled,
    ordersRejected: wire.orders_rejected,
    ordersCancelled: wire.orders_cancelled,
    fillRatioPercent: wire.fill_ratio_percent,
    dailyReturnPercent: wire.daily_return_percent,
    maxDrawdown: wire.max_drawdown,
    averageExecutionLatencySeconds: wire.average_execution_latency_seconds,
    winRatePercent: wire.win_rate_percent,
  }
}

export function mapRuntimeStats(wire: WireRuntimeStats): RuntimeStats {
  return {
    sessionState: wire.session_state as RuntimeStats['sessionState'],
    replaySpeed: wire.replay_speed as RuntimeStats['replaySpeed'],
    processedCandles: wire.processed_candles,
    totalCandles: wire.total_candles,
    eventsPublished: wire.events_published,
    ordersGenerated: wire.orders_generated,
    uptimeSeconds: wire.uptime_seconds,
  }
}

export function mapDashboardSnapshot(wire: WireDashboardSnapshot): DashboardSnapshot {
  return {
    runtime: mapRuntimeStats(wire.runtime),
    currentCandle: wire.current_candle ? mapCandle(wire.current_candle) : null,
    marketContext: wire.market_context ? mapMarketContext(wire.market_context) : null,
    latestSignal: wire.latest_signal ? mapSignal(wire.latest_signal) : null,
    latestRiskDecision: wire.latest_risk_decision
      ? mapRiskDecision(wire.latest_risk_decision)
      : null,
    latestRecommendation: wire.latest_recommendation
      ? mapRecommendation(wire.latest_recommendation)
      : null,
    orders: wire.orders.map(mapOrder),
    positions: wire.positions.map(mapPosition),
    portfolio: mapPortfolio(wire.portfolio),
    journal: wire.journal.map(mapJournalEntry),
    health: mapHealth(wire.health),
    performance: mapPerformance(wire.performance),
  }
}
