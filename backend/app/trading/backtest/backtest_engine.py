"""
Orchestrates a historical backtest by replaying candles one at a time
through the existing, already-approved trading pipeline:

    Historical Candles -> Replay -> Indicator Engine -> Market Context
    -> Trading Conditions -> Strategy Engine -> Risk Engine
    -> Decision Engine -> Trade Executor -> Performance Report

This module calculates no indicator, evaluates no strategy rule, and
performs no risk calculation itself - every one of those is a call
into the package that already owns it (Phases 5-10). It only decides
*when* to call them (candle by candle), tracks the running capital and
open position between calls, and hands the resulting trade history to
`performance.py`/`report.py`.

Long-only for this phase, per the CTO brief: a recommendation is only
ever acted on when its direction is Long.

Phase 16 (Grid Search Strategy Optimization Engine): `registry` is now
built from `config.strategy_parameters` instead of the parameterless
`default_registry()`, and `ema_period` is now threaded through to
`calculate_indicator_snapshot()`, both via a CTO-authorized narrow
exception to this package's freeze - `config.strategy_parameters=None`
(the default) reproduces `default_registry()`'s exact prior behavior,
and `config.ema_period` defaults to 20, the indicator engine's own
existing default. See `docs/OPTIMIZATION_GUIDE.md`.

Session status per candle is derived via
`app.market_data.market_session.market_session_service.get_status(candle.timestamp)`
- reused as-is, not reimplemented - which reads `app.core.config.settings.market_open`/
`market_close` (global app configuration), not `BacktestConfig.market_open`/
`market_close` (this run's configuration). They default to the same
"09:15"/"15:30" values, so this is invisible in the common case; a
backtest run with a `BacktestConfig` using different market hours than
the global settings would see a mismatch between session status and
the trading-window check. Not fixed here, since `MarketSessionService`
is an already-approved module this phase must not redesign - flagging
the coupling so it isn't a silent surprise.
"""

from datetime import date, datetime

from app.market_data.market_session import market_session_service
from app.market_data.schemas import Candle
from app.trading.backtest.models import BacktestConfig, BacktestResult, BacktestTrade, EquityPoint
from app.trading.backtest.performance import build_performance_report, compute_daily_pnl
from app.trading.backtest.trade_executor import (
    OpenPosition,
    build_open_position,
    check_exit,
    force_close,
)
from app.trading.conditions.engine import build_trading_conditions
from app.trading.context.engine import build_market_context
from app.trading.decision.engine import build_trade_recommendation
from app.trading.decision.models import StrategyCandidate
from app.trading.indicators.engine import calculate_indicator_snapshot
from app.trading.risk.engine import build_risk_assessment
from app.trading.risk.models import CapitalState
from app.trading.strategy.ema_breakout import EMABreakoutStrategy
from app.trading.strategy.engine import run_strategies
from app.trading.strategy.models import StrategyDirection
from app.trading.strategy.registry import StrategyRegistry


def run_backtest(candles: list[Candle], config: BacktestConfig) -> BacktestResult:
    if len(candles) <= config.warmup_candles:
        raise ValueError(
            f"Need more than {config.warmup_candles} candles "
            f"(warmup_candles), got {len(candles)}"
        )

    registry = StrategyRegistry()
    registry.register(EMABreakoutStrategy(config.strategy_parameters))

    capital = config.initial_capital
    open_position: OpenPosition | None = None
    trades: list[BacktestTrade] = []
    equity_curve: list[EquityPoint] = []
    last_trade_closed_at: datetime | None = None

    current_date: date | None = None
    trades_taken_today = 0
    realized_loss_today = 0.0

    for i in range(config.warmup_candles, len(candles)):
        candle = candles[i]

        candle_date = candle.timestamp.date()
        if candle_date != current_date:
            current_date = candle_date
            trades_taken_today = 0
            realized_loss_today = 0.0

        if open_position is not None:
            closed_trade = check_exit(open_position, candle, config.market_close)
            if closed_trade is not None:
                trades.append(closed_trade)
                capital += closed_trade.pnl
                trades_taken_today += 1
                realized_loss_today += max(0.0, -closed_trade.pnl)
                last_trade_closed_at = closed_trade.exit_time
                open_position = None

        if open_position is None:
            history = candles[: i + 1]

            snapshot = calculate_indicator_snapshot(
                history,
                total_call_oi=config.total_call_oi,
                total_put_oi=config.total_put_oi,
                price_change=config.price_change,
                oi_change=config.oi_change,
                ema_period=config.ema_period,
            )
            session_state = market_session_service.get_status(candle.timestamp)
            market_context = build_market_context(snapshot, session_state)
            trading_conditions = build_trading_conditions(
                session_state=session_state,
                current_timestamp=candle.timestamp,
                market_context=market_context,
                market_open=config.market_open,
                market_close=config.market_close,
                opening_range_minutes=config.opening_range_minutes,
                no_trade_zone_minutes=config.no_trade_zone_minutes,
                has_open_position=False,
                last_trade_closed_at=last_trade_closed_at,
                cooldown_minutes=config.cooldown_minutes,
                volume=candle.volume,
                min_volume=config.min_volume,
            )
            strategy_evaluations = run_strategies(
                registry, snapshot, market_context, trading_conditions
            )

            capital_state = CapitalState(
                total_capital=capital,
                capital_deployed=0.0,
                realized_loss_today=realized_loss_today,
                trades_taken_today=trades_taken_today,
                open_positions=0,
            )

            candidates = [
                StrategyCandidate(
                    evaluation=evaluation,
                    risk_assessment=build_risk_assessment(
                        strategy_evaluation=evaluation,
                        entry_price=snapshot.close_price,
                        atr=snapshot.atr,
                        config=config.risk_config,
                        capital_state=capital_state,
                    ),
                )
                for evaluation in strategy_evaluations
            ]

            recommendation = build_trade_recommendation(
                candidates=candidates, trading_conditions=trading_conditions
            )

            if (
                recommendation.recommended
                and recommendation.direction == StrategyDirection.LONG
                and recommendation.risk_summary is not None
                and recommendation.risk_summary.position_size >= 1
            ):
                open_position = build_open_position(
                    recommendation, candle.timestamp, snapshot.close_price
                )

        equity = capital
        if open_position is not None:
            equity += (candle.close - open_position.entry_price) * open_position.quantity
        equity_curve.append(EquityPoint(timestamp=candle.timestamp, equity=equity))

    if open_position is not None:
        closed_trade = force_close(open_position, candles[-1])
        trades.append(closed_trade)
        capital += closed_trade.pnl
        equity_curve.append(EquityPoint(timestamp=candles[-1].timestamp, equity=capital))

    report = build_performance_report(config.initial_capital, capital, trades, equity_curve)

    return BacktestResult(
        config=config,
        trades=trades,
        equity_curve=equity_curve,
        daily_pnl=compute_daily_pnl(trades),
        report=report,
    )
