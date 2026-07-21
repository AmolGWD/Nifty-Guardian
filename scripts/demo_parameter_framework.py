#!/usr/bin/env python3
"""
Standalone demonstration of the Parameter Injection Framework
(Phase 15).

Loads the default configuration for every config model, prints every
parameter in the catalog, overrides selected values, validates a
deliberately invalid combination, then injects both the default and the
overridden configuration into EMABreakoutStrategy against the same
IndicatorSnapshot/MarketContext/TradingConditions - so the strategy
visibly reads different values instead of just holding onto them
unused.

No optimization happens here - this only demonstrates that a
configuration can be built, validated, and injected. Requires no
Zerodha credentials, no network access, and no FastAPI server. Run from
anywhere:

    python3 scripts/demo_parameter_framework.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from pydantic import ValidationError  # noqa: E402

from app.config.parameter_catalog import PARAMETER_CATALOG  # noqa: E402
from app.config.risk_config import RiskParameters  # noqa: E402
from app.config.session_config import SessionParameters  # noqa: E402
from app.config.strategy_config import StrategyParameters  # noqa: E402
from app.market_data.market_session import MarketSessionStatus  # noqa: E402
from app.market_data.schemas import Candle  # noqa: E402
from app.trading.conditions.engine import build_trading_conditions  # noqa: E402
from app.trading.context.engine import build_market_context  # noqa: E402
from app.trading.indicators.engine import calculate_indicator_snapshot  # noqa: E402
from app.trading.strategy.ema_breakout import EMABreakoutStrategy  # noqa: E402

MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"


def _print_header(title: str) -> None:
    banner = "=" * 70
    print(f"\n{banner}\n{title}\n{banner}")


def build_sample_candles() -> list[Candle]:
    """25 synthetic 15-minute candles in a clear uptrend (see scripts/demo_pipeline.py)."""
    candles = []
    timestamp = datetime(2026, 7, 21, 9, 15)
    close = 100.0

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

    return candles


def main() -> None:
    _print_header("1. Load default configuration")
    strategy_defaults = StrategyParameters()
    risk_defaults = RiskParameters()
    session_defaults = SessionParameters()
    print(f"StrategyParameters (default): {strategy_defaults}")
    print(f"RiskParameters (default):     {risk_defaults}")
    print(f"SessionParameters (default):  {session_defaults}")

    _print_header("2. Print every parameter in the catalog")
    print(f"{'Name':<32}{'Default':<12}{'Safe to optimize':<18}{'Owning module'}")
    for entry in PARAMETER_CATALOG:
        print(
            f"{entry.name:<32}{entry.default_value:<12}"
            f"{entry.safe_to_optimize:<18}{entry.owning_module}"
        )

    _print_header("3. Override selected values")
    overridden = StrategyParameters(
        rsi_bullish_threshold=50.0,
        supertrend_enabled=False,
        min_agreeing_checks=3,
    )
    print(f"Overridden StrategyParameters: {overridden}")

    print("\nAttempting an invalid override (min_agreeing_checks=5 with only 3 checks enabled):")
    try:
        StrategyParameters(vwap_enabled=False, supertrend_enabled=False, min_agreeing_checks=5)
    except ValidationError as exc:
        print(f"  Rejected as expected: {exc.errors()[0]['ctx']['error']}")

    _print_header("4. Inject configuration into EMABreakoutStrategy")
    candles = build_sample_candles()
    snapshot = calculate_indicator_snapshot(
        candles, total_call_oi=120_000, total_put_oi=180_000, price_change=5.0, oi_change=10.0
    )
    session_state = MarketSessionStatus.OPEN
    context = build_market_context(snapshot, session_state)
    conditions = build_trading_conditions(
        session_state=session_state,
        current_timestamp=datetime(2026, 7, 21, 11, 0),
        market_context=context,
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
    )
    # Overwrite the sample's own RSI so it lands in the "inconclusive under
    # defaults, but bullish once the threshold is lowered" gap on purpose.
    snapshot = snapshot.model_copy(update={"rsi": 52.0})

    default_strategy = EMABreakoutStrategy()
    overridden_strategy = EMABreakoutStrategy(overridden)

    _print_header("5. Show the strategy receiving the configuration")
    default_evaluation = default_strategy.evaluate(snapshot, context, conditions)
    overridden_evaluation = overridden_strategy.evaluate(snapshot, context, conditions)

    print("Same IndicatorSnapshot (RSI=52.0), two different configurations:\n")
    print("Default StrategyParameters (rsi_bullish_threshold=55.0, supertrend_enabled=True):")
    print(
        f"  direction={default_evaluation.direction}, strength={default_evaluation.strength}, "
        f"valid={default_evaluation.valid}"
    )
    print(f"  reasons={default_evaluation.reasons}")
    print(f"  warnings={default_evaluation.warnings}")

    print(
        "\nOverridden StrategyParameters "
        "(rsi_bullish_threshold=50.0, supertrend_enabled=False, min_agreeing_checks=3):"
    )
    print(
        f"  direction={overridden_evaluation.direction}, "
        f"strength={overridden_evaluation.strength}, valid={overridden_evaluation.valid}"
    )
    print(f"  reasons={overridden_evaluation.reasons}")
    print(f"  warnings={overridden_evaluation.warnings}")

    print(
        "\nRSI 52.0 is inconclusive under the default 55/45 thresholds, but confirms Long "
        "once rsi_bullish_threshold is lowered to 50.0, and SuperTrend no longer votes once "
        "supertrend_enabled=False - the strategy is genuinely reading the injected "
        "configuration, not just holding onto it."
    )

    _print_header("Demo complete - no optimization performed, only configuration injection")


if __name__ == "__main__":
    main()
