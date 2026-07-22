#!/usr/bin/env python3
"""
Standalone demonstration of the Monte Carlo Analysis Framework
(Phase 18).

Runs a real backtest against a small synthetic dataset, then runs 100
Monte Carlo simulations against its trade outcomes with Trade Order
Shuffle, 0.10% slippage, and 1% missed trades enabled - printing the
mean return, 95% confidence interval, worst drawdown, probability of
profit, and top risk metrics.

Requires no Zerodha credentials, no network access, and no FastAPI
server. Run from anywhere:

    python3 scripts/demo_monte_carlo.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.market_data.schemas import Candle  # noqa: E402
from app.monte_carlo.models import PerturbationConfig  # noqa: E402
from app.monte_carlo.perturbations.missed_trade import MissedTradeConfig  # noqa: E402
from app.monte_carlo.perturbations.slippage import SlippageConfig  # noqa: E402
from app.monte_carlo.report import build_report, render_markdown  # noqa: E402
from app.monte_carlo.runner import run_monte_carlo_simulation  # noqa: E402
from app.trading.backtest.backtest_engine import run_backtest  # noqa: E402
from app.trading.backtest.models import BacktestConfig  # noqa: E402
from app.trading.risk.models import RiskConfig  # noqa: E402


def _print_header(title: str) -> None:
    banner = "=" * 70
    print(f"\n{banner}\n{title}\n{banner}")


def build_weekday_candles(num_days: int, start: datetime) -> list[Candle]:
    """Consecutive weekdays only, a clear uptrend each day (see docs/MONTE_CARLO_GUIDE.md)."""
    candles: list[Candle] = []
    close = 100.0
    day = start

    while len(candles) < num_days * 25:
        if day.isoweekday() in (6, 7):
            day += timedelta(days=1)
            continue

        timestamp = day
        for i in range(25):
            open_price = close
            close = close - 1.0 if i % 6 == 5 else close + 2.5
            high = max(open_price, close) + 1.0
            low = min(open_price, close) - 1.0
            volume = 10_000 + (i * 500)
            candles.append(
                Candle(
                    timestamp=timestamp, open=open_price, high=high, low=low, close=close,
                    volume=volume,
                )
            )
            timestamp += timedelta(minutes=15)
        day += timedelta(days=1)

    return candles


def main() -> None:
    _print_header("1. Run the underlying backtest")
    candles = build_weekday_candles(10, start=datetime(2026, 1, 5, 9, 15))  # a Monday
    backtest_config = BacktestConfig(initial_capital=100_000.0, risk_config=RiskConfig())
    backtest_result = run_backtest(candles, backtest_config)
    print(f"Trades: {backtest_result.report.total_trades}")
    print(f"Net profit: {backtest_result.report.net_profit:.4f}")
    print(f"Max drawdown: {backtest_result.report.max_drawdown:.4f}")

    _print_header("2. Run 100 Monte Carlo simulations")
    perturbation_config = PerturbationConfig(
        trade_shuffle_enabled=True,
        slippage=SlippageConfig(entry_slippage_percent=0.10, exit_slippage_percent=0.10),
        missed_trades=MissedTradeConfig(miss_probability_percent=1.0),
    )
    print("Perturbations: Trade Order Shuffle, 0.10% slippage, 1% missed trades")

    run = run_monte_carlo_simulation(
        backtest_result=backtest_result,
        perturbation_config=perturbation_config,
        num_simulations=100,
        seed=42,
        candles=candles,
    )
    print(f"Completed {run.num_simulations} simulations in {run.duration_seconds:.3f}s")

    report = build_report(run)
    stats = report.statistics

    _print_header("3. Results")
    print(f"Mean return: {stats.mean_return_percent:.4f}%")
    print(
        f"95% confidence interval: [{stats.confidence_interval.lower_bound:.4f}%, "
        f"{stats.confidence_interval.upper_bound:.4f}%]"
    )
    print(f"Worst drawdown: {stats.worst_drawdown:.4f}")
    print(f"Probability of profit: {stats.probability_of_profit_percent:.2f}%")

    _print_header("4. Top risk metrics")
    print(f"Probability of loss: {stats.probability_of_loss_percent:.2f}%")
    print(f"Value at Risk (VaR): {stats.value_at_risk_percent:.4f}%")
    print(f"Conditional VaR (CVaR): {stats.conditional_value_at_risk_percent:.4f}%")
    print(f"Worst return: {stats.worst_return_percent:.4f}%")
    print(f"Best return: {stats.best_return_percent:.4f}%")

    _print_header("FULL REPORT (MARKDOWN)")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
