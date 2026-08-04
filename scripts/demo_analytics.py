#!/usr/bin/env python3
"""
Standalone demonstration of the Advanced Backtesting Analytics
Framework.

Loads the same sample historical data used by `scripts/demo_backtest.py`,
runs a complete backtest to produce a BacktestResult, then runs that
result through `app.trading.analytics.analytics_engine.build_analytics_report()`
and prints the full analytics report (overall performance, yearly and
monthly breakdowns, market regime analysis, time analysis, trade
distribution, risk analysis, strategy breakdown, and ASCII charts).

Requires no Zerodha credentials, no network access, and no FastAPI
server. Run from anywhere:

    python3 scripts/demo_analytics.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.trading.analytics.analytics_engine import build_analytics_report  # noqa: E402
from app.trading.analytics.report_builder import format_analytics_report  # noqa: E402
from app.trading.backtest.backtest_engine import run_backtest  # noqa: E402
from app.trading.backtest.loader import load_candles_from_csv  # noqa: E402
from app.trading.backtest.models import BacktestConfig  # noqa: E402
from app.trading.risk.models import RiskConfig  # noqa: E402

SAMPLE_CSV = _BACKEND_DIR / "app" / "market_data" / "sample_data" / "nifty_sample_candles.csv"


def main() -> None:
    candles = load_candles_from_csv(SAMPLE_CSV)
    print(f"Loaded {len(candles)} candles from {SAMPLE_CSV.name}")
    print(f"Range: {candles[0].timestamp} -> {candles[-1].timestamp}\n")

    config = BacktestConfig(
        initial_capital=100_000.0,
        risk_config=RiskConfig(
            risk_per_trade_percent=1.0,
            stop_loss_atr_multiplier=1.5,
            target_atr_multiplier=3.0,
            max_daily_loss=5_000.0,
            max_trades_per_day=5,
            max_concurrent_positions=1,
            max_capital_exposure_percent=100.0,
        ),
    )

    result = run_backtest(candles, config)
    analytics = build_analytics_report(result, candles)

    print(format_analytics_report(analytics, result))


if __name__ == "__main__":
    main()
