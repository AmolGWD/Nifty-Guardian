#!/usr/bin/env python3
"""
Standalone demonstration of the Historical Backtesting Engine.

Loads sample historical candles from
`backend/app/market_data/sample_data/nifty_sample_candles.csv`,
runs a complete backtest through the existing trading pipeline
(app.trading.backtest.backtest_engine.run_backtest - which itself calls
Indicators, Market Context, Trading Conditions, Strategy Engine, Risk
Engine, and Decision Engine, exactly as they already exist), and prints
a readable summary plus the first five completed trades.

Requires no Zerodha credentials, no network access, and no FastAPI
server. Run from anywhere:

    python3 scripts/demo_backtest.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.trading.backtest.backtest_engine import run_backtest  # noqa: E402
from app.trading.backtest.loader import load_candles_from_csv  # noqa: E402
from app.trading.backtest.models import BacktestConfig  # noqa: E402
from app.trading.backtest.report import format_report, format_trade  # noqa: E402
from app.trading.risk.models import RiskConfig  # noqa: E402

SAMPLE_CSV = _BACKEND_DIR / "app" / "market_data" / "sample_data" / "nifty_sample_candles.csv"


def main() -> None:
    candles = load_candles_from_csv(SAMPLE_CSV)
    print(f"Loaded {len(candles)} candles from {SAMPLE_CSV.name}")
    print(f"Range: {candles[0].timestamp} -> {candles[-1].timestamp}")

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

    print(format_report(result))

    print("\nFirst 5 completed trades:")
    for index, trade in enumerate(result.trades[:5], start=1):
        print(format_trade(trade, index))

    if not result.trades:
        print("(no trades were taken during this run)")


if __name__ == "__main__":
    main()
