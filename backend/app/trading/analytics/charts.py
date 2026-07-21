"""
Console-friendly, text-only charts - no external plotting libraries.
Equity/drawdown curves are downsampled to `width` columns before
rendering, so a chart stays readable (and cheap to build) regardless
of how many candles/years of history produced it.
"""

from app.trading.analytics.models import MonthlyPerformance, TradeDistribution
from app.trading.backtest.models import EquityPoint


def _downsample(values: list[float], width: int) -> list[float]:
    if len(values) <= width:
        return values

    step = len(values) / width
    return [values[int(i * step)] for i in range(width)]


def _render_line_chart(values: list[float], width: int, height: int) -> str:
    if not values:
        return "(no data)"

    sampled = _downsample(values, width)
    low = min(sampled)
    high = max(sampled)
    span = high - low if high != low else 1.0

    rows = []
    for row in range(height, 0, -1):
        threshold = low + span * (row / height)
        line = "".join("*" if value >= threshold else " " for value in sampled)
        rows.append(f"{threshold:>14,.2f} |{line}")
    rows.append(" " * 15 + "+" + "-" * len(sampled))
    return "\n".join(rows)


def render_equity_curve(equity_curve: list[EquityPoint], width: int = 60, height: int = 15) -> str:
    values = [point.equity for point in equity_curve]
    return _render_line_chart(values, width, height)


def render_drawdown_curve(
    equity_curve: list[EquityPoint], width: int = 60, height: int = 10
) -> str:
    return _render_line_chart(_drawdown_percent_series(equity_curve), width, height)


def _drawdown_percent_series(equity_curve: list[EquityPoint]) -> list[float]:
    series = []
    peak: float | None = None
    for point in equity_curve:
        peak = point.equity if peak is None else max(peak, point.equity)
        drawdown_percent = ((peak - point.equity) / peak * 100) if peak else 0.0
        series.append(drawdown_percent)
    return series


def render_monthly_returns(monthly: list[MonthlyPerformance], width: int = 40) -> str:
    if not monthly:
        return "(no data)"

    max_abs_return = max(abs(period.return_percent) for period in monthly) or 1.0

    lines = []
    for period in monthly:
        bar_length = int(abs(period.return_percent) / max_abs_return * width)
        bar_char = "+" if period.return_percent >= 0 else "-"
        lines.append(
            f"{period.year}-{period.month:02d}  {period.return_percent:+7.2f}%  "
            f"{bar_char * bar_length}"
        )
    return "\n".join(lines)


def render_trade_distribution(distribution: TradeDistribution, width: int = 40) -> str:
    lines = ["Exit Reasons:"]
    for bucket in distribution.by_exit_reason:
        bar_length = int(bucket.percentage / 100 * width)
        lines.append(f"  {bucket.exit_reason:<12} {bucket.percentage:6.2f}%  {'#' * bar_length}")

    lines.append("")
    lines.append("Direction:")
    for direction_bucket in distribution.by_direction:
        lines.append(
            f"  {direction_bucket.direction.value:<8} trades={direction_bucket.trade_count} "
            f"win_rate={direction_bucket.win_rate:.2f}% net_pnl={direction_bucket.net_pnl:,.2f}"
        )

    return "\n".join(lines)
