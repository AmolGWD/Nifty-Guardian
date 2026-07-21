from datetime import datetime

import pytest

from app.trading.backtest.models import ExitReason
from app.trading.backtest.trade_executor import build_open_position, check_exit, force_close
from app.trading.decision.models import RecommendationStrength, TradeRecommendation
from app.trading.risk.models import RiskAssessment
from app.trading.strategy.models import StrategyDirection
from tests.trading.backtest.helpers import make_backtest_candles


def make_recommendation(
    *,
    recommended: bool = True,
    direction: StrategyDirection = StrategyDirection.LONG,
    stop_loss: float = 97.0,
    target: float = 106.0,
    position_size: int = 100,
    reward_risk_ratio: float = 2.0,
) -> TradeRecommendation:
    return TradeRecommendation(
        recommended=recommended,
        direction=direction,
        selected_strategy="EMABreakout",
        recommendation_strength=RecommendationStrength.STRONG,
        reasons=[],
        warnings=[],
        risk_summary=RiskAssessment(
            risk_ok=True,
            position_size=position_size,
            stop_loss=stop_loss,
            target=target,
            reward_risk_ratio=reward_risk_ratio,
            capital_required=position_size * 100.0,
            rejection_reasons=[],
        ),
    )


def test_build_open_position_reads_risk_summary() -> None:
    recommendation = make_recommendation(stop_loss=97.0, target=106.0, position_size=157)

    position = build_open_position(recommendation, datetime(2026, 7, 21, 10, 0), 100.0)

    assert position.strategy_name == "EMABreakout"
    assert position.direction == StrategyDirection.LONG
    assert position.entry_price == 100.0
    assert position.stop_loss == 97.0
    assert position.target == 106.0
    assert position.quantity == 157


def test_build_open_position_rejects_non_long_direction() -> None:
    recommendation = make_recommendation(direction=StrategyDirection.SHORT)

    with pytest.raises(AssertionError):
        build_open_position(recommendation, datetime(2026, 7, 21, 10, 0), 100.0)


def test_check_exit_triggers_stop_loss() -> None:
    recommendation = make_recommendation(stop_loss=97.0, target=106.0)
    position = build_open_position(recommendation, datetime(2026, 7, 21, 10, 0), 100.0)
    candle = make_backtest_candles(
        [(99.0, 99.5, 96.0, 96.5, 1000)], start=datetime(2026, 7, 21, 10, 15)
    )[0]

    trade = check_exit(position, candle, "15:30")

    assert trade is not None
    assert trade.exit_reason == ExitReason.STOP_LOSS
    assert trade.exit_price == 97.0
    assert trade.pnl == (97.0 - 100.0) * position.quantity


def test_check_exit_triggers_target() -> None:
    recommendation = make_recommendation(stop_loss=97.0, target=106.0)
    position = build_open_position(recommendation, datetime(2026, 7, 21, 10, 0), 100.0)
    candle = make_backtest_candles(
        [(104.0, 107.0, 103.5, 106.5, 1000)], start=datetime(2026, 7, 21, 10, 15)
    )[0]

    trade = check_exit(position, candle, "15:30")

    assert trade is not None
    assert trade.exit_reason == ExitReason.TARGET
    assert trade.exit_price == 106.0
    assert trade.pnl == (106.0 - 100.0) * position.quantity


def test_check_exit_prefers_stop_loss_when_both_touched() -> None:
    recommendation = make_recommendation(stop_loss=97.0, target=106.0)
    position = build_open_position(recommendation, datetime(2026, 7, 21, 10, 0), 100.0)
    candle = make_backtest_candles(
        [(100.0, 110.0, 90.0, 105.0, 1000)], start=datetime(2026, 7, 21, 10, 15)
    )[0]

    trade = check_exit(position, candle, "15:30")

    assert trade is not None
    assert trade.exit_reason == ExitReason.STOP_LOSS


def test_check_exit_forces_end_of_day_exit() -> None:
    recommendation = make_recommendation(stop_loss=90.0, target=120.0)
    position = build_open_position(recommendation, datetime(2026, 7, 21, 10, 0), 100.0)
    candle = make_backtest_candles(
        [(101.0, 102.0, 100.5, 101.5, 1000)], start=datetime(2026, 7, 21, 15, 30)
    )[0]

    trade = check_exit(position, candle, "15:30")

    assert trade is not None
    assert trade.exit_reason == ExitReason.END_OF_DAY
    assert trade.exit_price == 101.5


def test_check_exit_returns_none_when_nothing_triggers() -> None:
    recommendation = make_recommendation(stop_loss=90.0, target=120.0)
    position = build_open_position(recommendation, datetime(2026, 7, 21, 10, 0), 100.0)
    candle = make_backtest_candles(
        [(101.0, 102.0, 100.5, 101.5, 1000)], start=datetime(2026, 7, 21, 11, 0)
    )[0]

    assert check_exit(position, candle, "15:30") is None


def test_force_close_exits_at_candle_close() -> None:
    recommendation = make_recommendation(stop_loss=90.0, target=120.0)
    position = build_open_position(recommendation, datetime(2026, 7, 21, 10, 0), 100.0)
    candle = make_backtest_candles(
        [(101.0, 102.0, 100.5, 101.5, 1000)], start=datetime(2026, 7, 21, 15, 15)
    )[0]

    trade = force_close(position, candle)

    assert trade.exit_reason == ExitReason.END_OF_DATA
    assert trade.exit_price == 101.5
