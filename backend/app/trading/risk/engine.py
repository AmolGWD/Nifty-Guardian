"""
Composes the independent risk evaluators into one RiskAssessment.

This does not approve or reject a trade - it evaluates risk only.
`risk_ok` reflects the four risk-limit gates (daily loss, max trades
per day, capital exposure, max concurrent positions) plus a minimum
viable position size; it deliberately ignores
`StrategyEvaluation.valid` entirely, per this phase's explicit
requirement to evaluate risk independently of strategy validity.
`StrategyEvaluation` is used only for `direction`, to place stop-loss
and target on the correct side of `entry_price`.

`entry_price` and `atr` are required, explicit parameters even though
neither appears in the phase's Inputs list (StrategyEvaluation,
TradingConditions, Configuration, Capital settings): none of position
sizing, stop-loss, target, reward/risk, or capital exposure can be
computed without knowing the price to enter at and a volatility measure
to size the stop distance from, and no listed input carries either.
`atr` is passed as a bare float (from `IndicatorSnapshot.atr`) rather
than the whole snapshot, keeping this package's only real dependency
surface `app.trading.strategy` (for `StrategyDirection`).

`TradingConditions` is intentionally not a parameter here: none of the
eight risk evaluators has a legitimate use for session/timing state,
and gating on it would reintroduce the "approve/reject" behavior this
phase explicitly rules out for strategy validity - the same principle
extends to trading permission. The layer that combines
`StrategyEvaluation`, `TradingConditions`, and `RiskAssessment` into an
actual go/no-go decision is later work.
"""

from app.trading.risk.capital_exposure import is_within_capital_exposure
from app.trading.risk.daily_loss_limit import is_within_daily_loss_limit
from app.trading.risk.max_concurrent_positions import is_within_max_concurrent_positions
from app.trading.risk.max_trades_per_day import is_within_max_trades_per_day
from app.trading.risk.models import CapitalState, RiskAssessment, RiskConfig, RiskRejectionReason
from app.trading.risk.position_sizing import calculate_position_size
from app.trading.risk.reward_risk import calculate_reward_risk_ratio
from app.trading.risk.stop_loss import calculate_stop_loss
from app.trading.risk.target import calculate_target
from app.trading.strategy.models import StrategyDirection, StrategyEvaluation


def build_risk_assessment(
    *,
    strategy_evaluation: StrategyEvaluation,
    entry_price: float,
    atr: float,
    config: RiskConfig,
    capital_state: CapitalState,
) -> RiskAssessment:
    direction = strategy_evaluation.direction

    stop_loss = calculate_stop_loss(entry_price, atr, config.stop_loss_atr_multiplier, direction)
    target = calculate_target(entry_price, atr, config.target_atr_multiplier, direction)

    stop_loss_distance = abs(entry_price - stop_loss)
    target_distance = abs(target - entry_price)

    reward_risk_ratio = calculate_reward_risk_ratio(stop_loss_distance, target_distance)
    position_size = calculate_position_size(
        capital_state.total_capital, config.risk_per_trade_percent, stop_loss_distance
    )
    capital_required = position_size * entry_price

    daily_loss_ok = is_within_daily_loss_limit(
        capital_state.realized_loss_today, config.max_daily_loss
    )
    max_trades_ok = is_within_max_trades_per_day(
        capital_state.trades_taken_today, config.max_trades_per_day
    )
    capital_exposure_ok = is_within_capital_exposure(
        capital_state.capital_deployed,
        capital_required,
        capital_state.total_capital,
        config.max_capital_exposure_percent,
    )
    concurrent_positions_ok = is_within_max_concurrent_positions(
        capital_state.open_positions, config.max_concurrent_positions
    )

    rejection_reasons: list[RiskRejectionReason] = []
    if not daily_loss_ok:
        rejection_reasons.append(RiskRejectionReason.DAILY_LOSS_LIMIT_EXCEEDED)
    if not max_trades_ok:
        rejection_reasons.append(RiskRejectionReason.MAX_TRADES_PER_DAY_REACHED)
    if not capital_exposure_ok:
        rejection_reasons.append(RiskRejectionReason.CAPITAL_EXPOSURE_EXCEEDED)
    if not concurrent_positions_ok:
        rejection_reasons.append(RiskRejectionReason.MAX_CONCURRENT_POSITIONS_REACHED)
    if direction != StrategyDirection.NONE and position_size < 1:
        rejection_reasons.append(RiskRejectionReason.POSITION_SIZE_TOO_SMALL)

    return RiskAssessment(
        risk_ok=len(rejection_reasons) == 0,
        position_size=position_size,
        stop_loss=stop_loss,
        target=target,
        reward_risk_ratio=reward_risk_ratio,
        capital_required=capital_required,
        rejection_reasons=rejection_reasons,
    )
