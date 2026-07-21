from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.config.strategy_config import StrategyParameters
from app.market_data.schemas import Candle
from app.trading.backtest.backtest_engine import run_backtest
from app.trading.backtest.models import BacktestResult, ExitReason
from app.trading.strategy.models import StrategyDirection
from tests.trading.backtest.helpers import make_backtest_config


def _build_two_day_uptrend_candles() -> list[Candle]:
    """
    50 candles across two consecutive weekdays (2026-07-21 Tuesday and
    2026-07-22 Wednesday), 25 candles per day at 15-minute intervals
    from market open (09:15) to 15:15 - a clear uptrend each day (with
    a small pullback every sixth candle so RSI doesn't cap at exactly
    100), enough for at least one full entry-to-exit cycle including
    an end-of-day forced exit.
    """
    candles: list[Candle] = []
    close = 100.0

    for day_offset in (0, 1):
        day_start = datetime(2026, 7, 21, 9, 15) + timedelta(days=day_offset)
        timestamp = day_start
        for i in range(25):
            open_price = close
            close = close - 1.0 if i % 6 == 5 else close + 2.5
            high = max(open_price, close) + 1.0
            low = min(open_price, close) - 1.0
            volume = 10_000 + (i * 500)
            candles.append(
                Candle(
                    timestamp=timestamp,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                )
            )
            timestamp += timedelta(minutes=15)

    return candles


def test_run_backtest_produces_a_complete_result() -> None:
    candles = _build_two_day_uptrend_candles()
    config = make_backtest_config()

    result = run_backtest(candles, config)

    assert isinstance(result, BacktestResult)
    assert len(result.trades) > 0


def test_run_backtest_final_capital_matches_sum_of_trade_pnl() -> None:
    candles = _build_two_day_uptrend_candles()
    config = make_backtest_config()

    result = run_backtest(candles, config)

    expected_final_capital = config.initial_capital + sum(t.pnl for t in result.trades)
    assert result.report.final_capital == pytest.approx(expected_final_capital)
    assert result.report.net_profit == pytest.approx(sum(t.pnl for t in result.trades))


def test_run_backtest_every_trade_is_long_only() -> None:
    candles = _build_two_day_uptrend_candles()
    config = make_backtest_config()

    result = run_backtest(candles, config)

    assert all(trade.direction == StrategyDirection.LONG for trade in result.trades)


def test_run_backtest_end_of_day_exits_happen_at_or_after_market_close() -> None:
    candles = _build_two_day_uptrend_candles()
    config = make_backtest_config()

    result = run_backtest(candles, config)

    end_of_day_exits = [t for t in result.trades if t.exit_reason == ExitReason.END_OF_DAY]
    for trade in end_of_day_exits:
        assert trade.exit_time.strftime("%H:%M") >= config.market_close


def test_run_backtest_equity_curve_covers_every_evaluated_candle() -> None:
    candles = _build_two_day_uptrend_candles()
    config = make_backtest_config()

    result = run_backtest(candles, config)

    evaluated_candles = len(candles) - config.warmup_candles
    assert len(result.equity_curve) >= evaluated_candles


def test_run_backtest_raises_with_too_few_candles() -> None:
    candles = _build_two_day_uptrend_candles()[:10]
    config = make_backtest_config(warmup_candles=20)

    with pytest.raises(ValueError):
        run_backtest(candles, config)


def test_backtest_result_is_immutable() -> None:
    candles = _build_two_day_uptrend_candles()
    config = make_backtest_config()

    result = run_backtest(candles, config)

    with pytest.raises(ValidationError):
        result.trades = []  # type: ignore[misc]


def test_default_strategy_parameters_reproduces_no_argument_behavior() -> None:
    """Phase 16: strategy_parameters=None (the default) must equal StrategyParameters()."""
    candles = _build_two_day_uptrend_candles()

    default_result = run_backtest(candles, make_backtest_config())
    explicit_config = make_backtest_config().model_copy(
        update={"strategy_parameters": StrategyParameters()}
    )
    explicit_result = run_backtest(candles, explicit_config)

    assert default_result.trades == explicit_result.trades
    assert default_result.report == explicit_result.report


def test_custom_strategy_parameters_changes_backtest_outcome() -> None:
    """An unreachable min_agreeing_checks must produce zero trades where the default trades."""
    candles = _build_two_day_uptrend_candles()
    config = make_backtest_config()

    default_result = run_backtest(candles, config)
    assert default_result.report.total_trades > 0

    unreachable_config = config.model_copy(
        update={
            "strategy_parameters": StrategyParameters(
                rsi_bullish_threshold=99.9, rsi_bearish_threshold=0.1, min_agreeing_checks=5
            )
        }
    )
    unreachable_result = run_backtest(candles, unreachable_config)

    assert unreachable_result.report.total_trades == 0


def test_custom_ema_period_changes_backtest_outcome() -> None:
    """A larger ema_period than the available warmup history must fail deterministically."""
    candles = _build_two_day_uptrend_candles()
    config = make_backtest_config(warmup_candles=20).model_copy(update={"ema_period": 25})

    with pytest.raises(ValueError, match="EMA"):
        run_backtest(candles, config)
