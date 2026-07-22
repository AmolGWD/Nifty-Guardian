from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.market_data.schemas import Candle
from app.monte_carlo.perturbations import execution_delay
from app.monte_carlo.perturbations.execution_delay import ExecutionDelayConfig
from tests.monte_carlo.helpers import make_trade


def _make_candles(
    closes: list[float], start: datetime = datetime(2026, 1, 5, 9, 15)
) -> list[Candle]:
    candles = []
    timestamp = start
    for close in closes:
        candles.append(
            Candle(timestamp=timestamp, open=close, high=close, low=close, close=close, volume=1000)
        )
        timestamp += timedelta(minutes=15)
    return candles


def test_delays_entry_and_exit_fill_to_a_later_candles_close() -> None:
    candles = _make_candles([100.0, 101.0, 102.0, 103.0, 104.0])
    trade = make_trade(
        entry_time=candles[0].timestamp, entry_price=100.0,
        exit_time=candles[2].timestamp, exit_price=102.0, quantity=10,
    )
    config = ExecutionDelayConfig(delay_candles=2)

    adjusted = execution_delay.apply([trade], candles, config)[0]

    assert adjusted.entry_price == candles[2].close  # entry candle index 0 + 2 -> index 2
    assert adjusted.exit_price == candles[4].close  # exit candle index 2 + 2 -> index 4


def test_pnl_is_recomputed_from_delayed_prices() -> None:
    candles = _make_candles([100.0, 101.0, 102.0, 103.0, 104.0])
    trade = make_trade(
        entry_time=candles[0].timestamp, entry_price=100.0,
        exit_time=candles[2].timestamp, exit_price=102.0, quantity=10,
    )
    config = ExecutionDelayConfig(delay_candles=2)

    adjusted = execution_delay.apply([trade], candles, config)[0]

    assert adjusted.pnl == pytest.approx((candles[4].close - candles[2].close) * 10)


def test_delay_past_end_of_data_keeps_original_price() -> None:
    candles = _make_candles([100.0, 101.0, 102.0])
    trade = make_trade(
        entry_time=candles[0].timestamp, entry_price=100.0,
        exit_time=candles[2].timestamp, exit_price=102.0, quantity=10,
    )
    config = ExecutionDelayConfig(delay_candles=10)

    adjusted = execution_delay.apply([trade], candles, config)[0]

    assert adjusted.entry_price == trade.entry_price
    assert adjusted.exit_price == trade.exit_price


def test_trade_timestamp_not_found_in_candles_keeps_original_price() -> None:
    candles = _make_candles([100.0, 101.0, 102.0])
    trade = make_trade(
        entry_time=datetime(2099, 1, 1), entry_price=100.0,
        exit_time=datetime(2099, 1, 1, 1), exit_price=105.0, quantity=10,
    )
    config = ExecutionDelayConfig(delay_candles=1)

    adjusted = execution_delay.apply([trade], candles, config)[0]

    assert adjusted.entry_price == trade.entry_price
    assert adjusted.exit_price == trade.exit_price


def test_rejects_non_positive_delay() -> None:
    with pytest.raises(ValidationError):
        ExecutionDelayConfig(delay_candles=0)
