"""
Buckets trade performance by time-of-day dimensions: hour, weekday,
session (Opening/Mid/Closing, relative to the backtest's own market
hours), and expiry day vs non-expiry day.

`by_expiry` is empty whenever `AnalyticsConfig.expiry_dates` is empty
(the default) - this generic CSV framework has no options-expiry
concept (same class of gap as the neutral PCR/OI defaults in
`app.trading.backtest.models.BacktestConfig`), so an empty result is
honest rather than a fabricated split.
"""

from app.trading.analytics.models import AnalyticsConfig, TimeAnalysis, TimeBucket
from app.trading.backtest.models import BacktestConfig, BacktestTrade

_WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def _minutes_since_midnight(hhmm: str) -> int:
    hour, minute = (int(part) for part in hhmm.split(":"))
    return hour * 60 + minute


def analyze_time(
    trades: list[BacktestTrade],
    backtest_config: BacktestConfig,
    analytics_config: AnalyticsConfig,
) -> TimeAnalysis:
    by_hour_groups: dict[str, list[BacktestTrade]] = {}
    by_weekday_groups: dict[str, list[BacktestTrade]] = {}
    by_session_groups: dict[str, list[BacktestTrade]] = {}
    by_expiry_groups: dict[str, list[BacktestTrade]] = {}

    market_open_minutes = _minutes_since_midnight(backtest_config.market_open)
    market_close_minutes = _minutes_since_midnight(backtest_config.market_close)
    opening_end = market_open_minutes + analytics_config.opening_session_minutes
    closing_start = market_close_minutes - analytics_config.closing_session_minutes

    for trade in trades:
        hour_label = trade.entry_time.strftime("%H:00")
        by_hour_groups.setdefault(hour_label, []).append(trade)

        weekday_label = _WEEKDAY_NAMES[trade.entry_time.weekday()]
        by_weekday_groups.setdefault(weekday_label, []).append(trade)

        entry_minutes = trade.entry_time.hour * 60 + trade.entry_time.minute
        if entry_minutes < opening_end:
            session_label = "Opening"
        elif entry_minutes >= closing_start:
            session_label = "Closing"
        else:
            session_label = "Mid"
        by_session_groups.setdefault(session_label, []).append(trade)

        if analytics_config.expiry_dates:
            expiry_label = (
                "ExpiryDay"
                if trade.entry_time.date() in analytics_config.expiry_dates
                else "NonExpiryDay"
            )
            by_expiry_groups.setdefault(expiry_label, []).append(trade)

    by_hour = _build_buckets(by_hour_groups)
    by_weekday = _build_buckets(by_weekday_groups)

    return TimeAnalysis(
        by_hour=by_hour,
        by_weekday=by_weekday,
        by_session=_build_buckets(by_session_groups),
        by_expiry=_build_buckets(by_expiry_groups),
        best_hour=_best(by_hour),
        worst_hour=_worst(by_hour),
        best_weekday=_best(by_weekday),
        worst_weekday=_worst(by_weekday),
    )


def _build_buckets(groups: dict[str, list[BacktestTrade]]) -> list[TimeBucket]:
    buckets = []
    for label, group_trades in groups.items():
        wins = [trade for trade in group_trades if trade.pnl > 0]
        buckets.append(
            TimeBucket(
                label=label,
                trade_count=len(group_trades),
                win_rate=round(len(wins) / len(group_trades) * 100, 4),
                net_pnl=round(sum(trade.pnl for trade in group_trades), 4),
            )
        )
    return buckets


def _best(buckets: list[TimeBucket]) -> str | None:
    if not buckets:
        return None
    return max(buckets, key=lambda bucket: bucket.net_pnl).label


def _worst(buckets: list[TimeBucket]) -> str | None:
    if not buckets:
        return None
    return min(buckets, key=lambda bucket: bucket.net_pnl).label
