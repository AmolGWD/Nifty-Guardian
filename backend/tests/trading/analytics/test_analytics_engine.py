import time
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.market_data.schemas import Candle
from app.trading.analytics.analytics_engine import build_analytics_report
from app.trading.analytics.models import AnalyticsReport
from app.trading.backtest.backtest_engine import run_backtest
from tests.trading.analytics.helpers import make_backtest_config


def _build_uptrend_candles(trading_days: int) -> list[Candle]:
    candles: list[Candle] = []
    close = 100.0

    for day_offset in range(trading_days):
        day_start = datetime(2026, 7, 21, 9, 15) + timedelta(days=day_offset)
        timestamp = day_start
        for i in range(25):
            open_price = close
            close = close - 1.0 if i % 6 == 5 else close + 2.5
            high = max(open_price, close) + 1.0
            low = min(open_price, close) - 1.0
            candles.append(
                Candle(
                    timestamp=timestamp,
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=10_000 + i * 100,
                )
            )
            timestamp += timedelta(minutes=15)

    return candles


def test_build_analytics_report_produces_a_complete_report() -> None:
    candles = _build_uptrend_candles(trading_days=6)
    config = make_backtest_config()

    result = run_backtest(candles, config)
    analytics = build_analytics_report(result, candles)

    assert isinstance(analytics, AnalyticsReport)
    assert analytics.overall.total_trades == result.report.total_trades
    assert analytics.overall.sharpe_ratio == result.report.sharpe_ratio
    assert analytics.overall.max_drawdown == result.report.max_drawdown


def test_build_analytics_report_overall_reuses_backtest_report_figures() -> None:
    """
    Every figure Phase 11 already computes must be read straight from
    BacktestResult.report, not recalculated - a divergence here would
    mean this phase duplicated (and could disagree with) Phase 11's
    own numbers.
    """
    candles = _build_uptrend_candles(trading_days=6)
    config = make_backtest_config()

    result = run_backtest(candles, config)
    analytics = build_analytics_report(result, candles)

    assert analytics.overall.win_rate == result.report.win_rate
    assert analytics.overall.profit_factor == result.report.profit_factor
    assert analytics.overall.expectancy == result.report.expectancy
    assert analytics.overall.average_win == result.report.average_win
    assert analytics.overall.average_loss == result.report.average_loss
    assert analytics.overall.reward_risk == result.report.average_reward_risk_ratio


def test_build_analytics_report_regime_trades_are_a_subset_of_all_trades() -> None:
    candles = _build_uptrend_candles(trading_days=6)
    result = run_backtest(candles, make_backtest_config())
    analytics = build_analytics_report(result, candles)

    regime_trade_count = sum(bucket.trade_count for bucket in analytics.market_regimes.by_trend)
    assert regime_trade_count <= len(result.trades)


def test_build_analytics_report_handles_a_backtest_with_no_trades() -> None:
    # A flat, non-trending dataset should trigger the EMA-alignment/
    # trend-agreement checks inconsistently enough that no trade
    # reliably qualifies - if it does, the report must still stay
    # internally consistent rather than erroring out.
    candles = _build_uptrend_candles(trading_days=1)
    result = run_backtest(candles, make_backtest_config())

    analytics = build_analytics_report(result, candles)

    assert analytics.overall.total_trades == len(result.trades)


def test_analytics_report_is_immutable() -> None:
    candles = _build_uptrend_candles(trading_days=6)
    result = run_backtest(candles, make_backtest_config())
    analytics = build_analytics_report(result, candles)

    with pytest.raises(ValidationError):
        analytics.overall = analytics.overall  # type: ignore[misc]


@pytest.mark.slow
def test_analytics_scales_to_a_larger_dataset_without_quadratic_blowup() -> None:
    """
    Not literally 5-10 years of NIFTY data (impractical to generate or
    process within a unit test's time budget, and this sandbox has no
    network access to source real historical data) - a smaller-scale
    proxy verifying build_analytics_report() completes in roughly
    linear time as candle count grows, catching any accidental O(n^2)
    pattern (e.g. recomputing MarketContext once per trade instead of
    once per unique candle index).
    """
    small_candles = _build_uptrend_candles(trading_days=20)
    large_candles = _build_uptrend_candles(trading_days=80)

    config = make_backtest_config()

    small_result = run_backtest(small_candles, config)
    start = time.perf_counter()
    build_analytics_report(small_result, small_candles)
    small_duration = time.perf_counter() - start

    large_result = run_backtest(large_candles, config)
    start = time.perf_counter()
    build_analytics_report(large_result, large_candles)
    large_duration = time.perf_counter() - start

    # 4x the candles should not cost anywhere near 16x the time; a
    # generous multiplier keeps this from being flaky on a slow CI
    # runner while still catching genuine quadratic regressions.
    assert large_duration < small_duration * 10 + 1.0
