from datetime import datetime

from app.trading.analytics.charts import (
    render_drawdown_curve,
    render_equity_curve,
    render_monthly_returns,
    render_trade_distribution,
)
from app.trading.analytics.models import MonthlyPerformance
from app.trading.analytics.trade_distribution import analyze_trade_distribution
from tests.trading.analytics.helpers import make_equity_point, make_trade


def test_render_equity_curve_produces_non_empty_output() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 9 + i, 0), equity=100_000.0 + i * 100)
        for i in range(5)
    ]

    output = render_equity_curve(curve, width=20, height=5)

    assert "*" in output
    assert len(output.splitlines()) == 6  # height rows + axis line


def test_render_equity_curve_handles_empty_curve() -> None:
    assert render_equity_curve([]) == "(no data)"


def test_render_equity_curve_downsamples_wide_data() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 9, 0) , equity=100_000.0 + i)
        for i in range(500)
    ]

    output = render_equity_curve(curve, width=30, height=5)

    # every row should be no wider than the requested sample width
    for line in output.splitlines()[:-1]:
        chart_part = line.split("|", 1)[1]
        assert len(chart_part) <= 30


def test_render_drawdown_curve_produces_output() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 9, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0), equity=95_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 11, 0), equity=100_000.0),
    ]

    output = render_drawdown_curve(curve, width=10, height=5)

    assert output != "(no data)"


def test_render_monthly_returns_shows_sign() -> None:
    monthly = [
        MonthlyPerformance(
            year=2026, month=7, trade_count=5, win_rate=60.0, net_pnl=500.0, return_percent=5.0
        ),
        MonthlyPerformance(
            year=2026, month=8, trade_count=3, win_rate=30.0, net_pnl=-200.0, return_percent=-2.0
        ),
    ]

    output = render_monthly_returns(monthly)

    assert "+5.00%" in output
    assert "-2.00%" in output


def test_render_monthly_returns_handles_empty_input() -> None:
    assert render_monthly_returns([]) == "(no data)"


def test_render_trade_distribution_includes_exit_reasons_and_direction() -> None:
    trades = [make_trade(pnl=500.0), make_trade(pnl=-100.0)]
    distribution = analyze_trade_distribution(trades)

    output = render_trade_distribution(distribution)

    assert "Exit Reasons:" in output
    assert "Direction:" in output
