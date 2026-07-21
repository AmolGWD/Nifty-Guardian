from app.trading.risk.models import CapitalState, RiskConfig
from app.trading.strategy.models import StrategyDirection, StrategyEvaluation, StrategyStrength


def make_strategy_evaluation(
    *,
    direction: StrategyDirection = StrategyDirection.LONG,
    strength: StrategyStrength = StrategyStrength.STRONG,
    valid: bool = True,
) -> StrategyEvaluation:
    return StrategyEvaluation(
        strategy_name="Test",
        valid=valid,
        direction=direction,
        strength=strength,
        reasons=[],
        warnings=[],
    )


def make_risk_config(
    *,
    risk_per_trade_percent: float = 1.0,
    stop_loss_atr_multiplier: float = 1.5,
    target_atr_multiplier: float = 3.0,
    max_daily_loss: float = 5000.0,
    max_trades_per_day: int = 5,
    max_concurrent_positions: int = 1,
    max_capital_exposure_percent: float = 50.0,
) -> RiskConfig:
    return RiskConfig(
        risk_per_trade_percent=risk_per_trade_percent,
        stop_loss_atr_multiplier=stop_loss_atr_multiplier,
        target_atr_multiplier=target_atr_multiplier,
        max_daily_loss=max_daily_loss,
        max_trades_per_day=max_trades_per_day,
        max_concurrent_positions=max_concurrent_positions,
        max_capital_exposure_percent=max_capital_exposure_percent,
    )


def make_capital_state(
    *,
    total_capital: float = 100_000.0,
    capital_deployed: float = 0.0,
    realized_loss_today: float = 0.0,
    trades_taken_today: int = 0,
    open_positions: int = 0,
) -> CapitalState:
    return CapitalState(
        total_capital=total_capital,
        capital_deployed=capital_deployed,
        realized_loss_today=realized_loss_today,
        trades_taken_today=trades_taken_today,
        open_positions=open_positions,
    )
