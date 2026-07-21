"""
Buckets trade performance by the market regime each trade was entered
in - Trend (Bullish/Bearish/Sideways), Volatility (High/Low), and
Momentum (Strong/Weak, standing in for "Strong Trend"/"Weak Trend" -
Phase 6's MomentumContext is exactly that dimension).

`BacktestResult` (frozen, Phase 11) does not itself retain a
`MarketContext` per trade - Phase 11 never needed one after deciding
whether to enter, so it was never stored. Rather than change that
frozen model to start retaining one (out of scope - Backtest Engine is
frozen this phase), this module recomputes `MarketContext` for exactly
the candle each trade entered on, by calling the same already-approved
`calculate_indicator_snapshot()`/`build_market_context()` functions
Backtest Engine itself calls - reuse, not a reimplementation of either.
It needs the original `candles` list (the same one `run_backtest()`
was given) as an extra input beyond `BacktestResult` for exactly this
reason.

Every trade's entry candle is looked up once via a timestamp->index
dict built in a single O(n) pass, and each unique index's MarketContext
is computed at most once (cached), even if several trades happen to
share one - keeping this practical across several years of candles
without any change to how Indicators/Context work.
"""

from app.market_data.market_session import market_session_service
from app.market_data.schemas import Candle
from app.trading.analytics.models import MarketRegimeAnalysis, RegimeBucket
from app.trading.backtest.models import BacktestConfig, BacktestTrade
from app.trading.context.engine import build_market_context
from app.trading.context.models import MarketContext
from app.trading.indicators.engine import calculate_indicator_snapshot


def analyze_market_regimes(
    trades: list[BacktestTrade], candles: list[Candle], config: BacktestConfig
) -> MarketRegimeAnalysis:
    index_by_timestamp = {candle.timestamp: index for index, candle in enumerate(candles)}
    context_cache: dict[int, MarketContext] = {}

    trend_groups: dict[str, list[BacktestTrade]] = {}
    volatility_groups: dict[str, list[BacktestTrade]] = {}
    momentum_groups: dict[str, list[BacktestTrade]] = {}

    for trade in trades:
        index = index_by_timestamp.get(trade.entry_time)
        if index is None or index < 20:
            continue

        if index not in context_cache:
            history = candles[: index + 1]
            snapshot = calculate_indicator_snapshot(
                history,
                total_call_oi=config.total_call_oi,
                total_put_oi=config.total_put_oi,
                price_change=config.price_change,
                oi_change=config.oi_change,
            )
            session_state = market_session_service.get_status(history[-1].timestamp)
            context_cache[index] = build_market_context(snapshot, session_state)

        context = context_cache[index]
        trend_groups.setdefault(context.trend.value, []).append(trade)
        volatility_groups.setdefault(context.volatility.value, []).append(trade)
        momentum_groups.setdefault(context.momentum.value, []).append(trade)

    return MarketRegimeAnalysis(
        by_trend=_build_buckets(trend_groups),
        by_volatility=_build_buckets(volatility_groups),
        by_momentum=_build_buckets(momentum_groups),
    )


def _build_buckets(groups: dict[str, list[BacktestTrade]]) -> list[RegimeBucket]:
    buckets = []
    for regime, group_trades in groups.items():
        wins = [trade for trade in group_trades if trade.pnl > 0]
        buckets.append(
            RegimeBucket(
                regime=regime,
                trade_count=len(group_trades),
                win_rate=round(len(wins) / len(group_trades) * 100, 4),
                net_pnl=round(sum(trade.pnl for trade in group_trades), 4),
            )
        )
    return buckets
