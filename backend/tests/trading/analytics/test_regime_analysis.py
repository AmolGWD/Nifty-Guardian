from datetime import datetime, timedelta

from app.market_data.schemas import Candle
from app.trading.analytics.regime_analysis import analyze_market_regimes
from app.trading.context.models import TrendContext
from tests.trading.analytics.helpers import make_backtest_config, make_trade


def _build_uptrend_candles(count: int = 30) -> list[Candle]:
    candles = []
    timestamp = datetime(2026, 7, 21, 9, 15)
    close = 100.0
    for i in range(count):
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


def test_analyze_market_regimes_classifies_a_trade_entered_in_an_uptrend() -> None:
    candles = _build_uptrend_candles(30)
    entry_candle = candles[25]
    trade = make_trade(entry_time=entry_candle.timestamp, pnl=500.0)

    result = analyze_market_regimes([trade], candles, make_backtest_config())

    trend_labels = {bucket.regime for bucket in result.by_trend}
    assert TrendContext.BULLISH_TREND.value in trend_labels
    assert result.by_volatility
    assert result.by_momentum


def test_analyze_market_regimes_skips_trades_before_warmup() -> None:
    candles = _build_uptrend_candles(30)
    early_candle = candles[5]  # index < 20, not enough history for indicators
    trade = make_trade(entry_time=early_candle.timestamp)

    result = analyze_market_regimes([trade], candles, make_backtest_config())

    assert result.by_trend == []
    assert result.by_volatility == []
    assert result.by_momentum == []


def test_analyze_market_regimes_skips_trades_with_no_matching_candle() -> None:
    candles = _build_uptrend_candles(30)
    trade = make_trade(entry_time=datetime(2099, 1, 1, 9, 15))

    result = analyze_market_regimes([trade], candles, make_backtest_config())

    assert result.by_trend == []


def test_analyze_market_regimes_handles_no_trades() -> None:
    candles = _build_uptrend_candles(30)

    result = analyze_market_regimes([], candles, make_backtest_config())

    assert result.by_trend == []
    assert result.by_volatility == []
    assert result.by_momentum == []
