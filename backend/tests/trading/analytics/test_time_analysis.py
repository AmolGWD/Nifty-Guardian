from datetime import date, datetime

from app.trading.analytics.models import AnalyticsConfig
from app.trading.analytics.time_analysis import analyze_time
from tests.trading.analytics.helpers import make_backtest_config, make_trade


def test_analyze_time_buckets_by_hour_and_weekday() -> None:
    trades = [
        make_trade(entry_time=datetime(2026, 7, 21, 9, 30), pnl=500.0),  # Tuesday, 09:00
        make_trade(entry_time=datetime(2026, 7, 21, 9, 45), pnl=-100.0),  # Tuesday, 09:00
        make_trade(entry_time=datetime(2026, 7, 22, 11, 0), pnl=300.0),  # Wednesday, 11:00
    ]

    result = analyze_time(trades, make_backtest_config(), AnalyticsConfig())

    hour_labels = {bucket.label: bucket for bucket in result.by_hour}
    assert hour_labels["09:00"].trade_count == 2
    assert hour_labels["09:00"].net_pnl == 400.0
    assert hour_labels["11:00"].trade_count == 1

    weekday_labels = {bucket.label for bucket in result.by_weekday}
    assert weekday_labels == {"Tuesday", "Wednesday"}
    assert result.best_hour == "09:00"  # net_pnl 400 beats 11:00's 300
    assert result.worst_hour == "11:00"


def test_analyze_time_buckets_by_session() -> None:
    config = make_backtest_config()  # market_open=09:15, market_close=15:30
    analytics_config = AnalyticsConfig(opening_session_minutes=30, closing_session_minutes=30)

    trades = [
        make_trade(entry_time=datetime(2026, 7, 21, 9, 20), pnl=100.0),  # Opening
        make_trade(entry_time=datetime(2026, 7, 21, 12, 0), pnl=100.0),  # Mid
        make_trade(entry_time=datetime(2026, 7, 21, 15, 10), pnl=100.0),  # Closing
    ]

    result = analyze_time(trades, config, analytics_config)

    session_labels = {bucket.label: bucket.trade_count for bucket in result.by_session}
    assert session_labels == {"Opening": 1, "Mid": 1, "Closing": 1}


def test_analyze_time_expiry_buckets_are_empty_without_expiry_dates() -> None:
    trades = [make_trade(entry_time=datetime(2026, 7, 21, 10, 0))]

    result = analyze_time(trades, make_backtest_config(), AnalyticsConfig())

    assert result.by_expiry == []


def test_analyze_time_expiry_buckets_split_when_expiry_dates_supplied() -> None:
    trades = [
        make_trade(entry_time=datetime(2026, 7, 21, 10, 0), pnl=100.0),
        make_trade(entry_time=datetime(2026, 7, 22, 10, 0), pnl=-50.0),
    ]
    analytics_config = AnalyticsConfig(expiry_dates=frozenset({date(2026, 7, 21)}))

    result = analyze_time(trades, make_backtest_config(), analytics_config)

    labels = {bucket.label: bucket.trade_count for bucket in result.by_expiry}
    assert labels == {"ExpiryDay": 1, "NonExpiryDay": 1}


def test_analyze_time_best_and_worst_are_none_with_no_trades() -> None:
    result = analyze_time([], make_backtest_config(), AnalyticsConfig())

    assert result.best_hour is None
    assert result.worst_hour is None
    assert result.best_weekday is None
    assert result.worst_weekday is None
