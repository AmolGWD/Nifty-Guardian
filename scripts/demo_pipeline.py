#!/usr/bin/env python3
"""
Standalone demonstration of the full NIFTY Guardian trading pipeline,
end to end, against deterministic sample data.

Does not require Zerodha (no `kiteconnect` import, no network access)
and does not call FastAPI (no HTTP server, no `app.api`) - it imports
the trading domain packages directly and drives them with hand-built
sample data, exactly as a future orchestration layer (Paper Trading)
eventually will.

Run from anywhere:

    python3 scripts/demo_pipeline.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from pydantic import BaseModel  # noqa: E402

from app.market_data.market_session import MarketSessionStatus  # noqa: E402
from app.market_data.schemas import Candle  # noqa: E402
from app.trading.conditions.engine import build_trading_conditions  # noqa: E402
from app.trading.context.engine import build_market_context  # noqa: E402
from app.trading.decision.engine import build_trade_recommendation  # noqa: E402
from app.trading.decision.models import StrategyCandidate  # noqa: E402
from app.trading.indicators.engine import calculate_indicator_snapshot  # noqa: E402
from app.trading.risk.engine import build_risk_assessment  # noqa: E402
from app.trading.risk.models import CapitalState, RiskConfig  # noqa: E402
from app.trading.strategy.engine import run_strategies  # noqa: E402
from app.trading.strategy.registry import default_registry  # noqa: E402

MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"


def _print_header(title: str) -> None:
    banner = "=" * 24
    print(f"\n{banner}")
    print(title)
    print(banner)


def _print_model(model: BaseModel) -> None:
    print(json.dumps(model.model_dump(mode="json"), indent=2))


def build_sample_candles() -> list[Candle]:
    """
    25 synthetic 15-minute candles, oldest first, starting at market
    open (09:15) - enough candles to satisfy every indicator's minimum
    window (EMA needs >= 20, RSI needs >= 15, SuperTrend needs > 10),
    with volume that grows over the session. Mostly rising, with a
    small pullback every sixth candle so RSI settles at a strong but
    realistic value instead of capping at exactly 100 - still a clear
    uptrend overall (the second half's range is well above the first
    half's), for an unambiguous bullish read at every pipeline stage.
    """
    candles = []
    timestamp = datetime(2026, 7, 21, 9, 15)  # a Tuesday - a valid trading day
    close = 100.0

    for i in range(25):
        open_price = close
        close = close - 1.0 if i % 6 == 5 else close + 2.5
        high = max(open_price, close) + 1.0
        low = min(open_price, close) - 1.0
        volume = 10_000 + (i * 500)

        candles.append(
            Candle(
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
        )
        timestamp += timedelta(minutes=15)

    return candles


def main() -> None:
    candles = build_sample_candles()

    _print_header("SAMPLE MARKET DATA")
    print(f"{len(candles)} candles, {candles[0].timestamp} -> {candles[-1].timestamp}")
    print(f"First close: {candles[0].close}, Last close: {candles[-1].close}")

    # Stage 1: Indicators
    snapshot = calculate_indicator_snapshot(
        candles,
        total_call_oi=120_000,
        total_put_oi=180_000,
        price_change=5.0,
        oi_change=10.0,
    )
    _print_header("INDICATORS")
    _print_model(snapshot)

    # Stage 2: Market Context
    session_state = MarketSessionStatus.OPEN
    market_context = build_market_context(snapshot, session_state)
    _print_header("MARKET CONTEXT")
    _print_model(market_context)

    # Stage 3: Trading Conditions - "now" is evaluated independently of
    # the candle history above (indicators look backward at what
    # already happened; conditions look at the current wall clock),
    # deliberately set well inside market hours - clear of both the
    # opening-range restriction (09:15-09:30) and the no-trade zone
    # (last 15 minutes before the 15:30 close).
    current_timestamp = datetime(2026, 7, 21, 11, 0)
    trading_conditions = build_trading_conditions(
        session_state=session_state,
        current_timestamp=current_timestamp,
        market_context=market_context,
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
    )
    _print_header("TRADING CONDITIONS")
    _print_model(trading_conditions)

    # Stage 4: Strategy Engine
    registry = default_registry()
    strategy_evaluations = run_strategies(registry, snapshot, market_context, trading_conditions)
    _print_header("STRATEGY EVALUATIONS")
    for evaluation in strategy_evaluations:
        _print_model(evaluation)

    # Stage 5: Risk Engine (one RiskAssessment per strategy candidate,
    # each computed against that strategy's own direction)
    risk_config = RiskConfig(
        risk_per_trade_percent=1.0,
        stop_loss_atr_multiplier=1.5,
        target_atr_multiplier=3.0,
        max_daily_loss=5_000.0,
        max_trades_per_day=5,
        max_concurrent_positions=1,
        max_capital_exposure_percent=50.0,
    )
    capital_state = CapitalState(
        total_capital=100_000.0,
        capital_deployed=0.0,
        realized_loss_today=0.0,
        trades_taken_today=0,
        open_positions=0,
    )

    candidates = []
    _print_header("RISK ASSESSMENTS")
    for evaluation in strategy_evaluations:
        risk_assessment = build_risk_assessment(
            strategy_evaluation=evaluation,
            entry_price=snapshot.close_price,
            atr=snapshot.atr,
            config=risk_config,
            capital_state=capital_state,
        )
        _print_model(risk_assessment)
        candidates.append(
            StrategyCandidate(evaluation=evaluation, risk_assessment=risk_assessment)
        )

    # Stage 6: Decision Engine
    recommendation = build_trade_recommendation(
        candidates=candidates, trading_conditions=trading_conditions
    )
    _print_header("TRADE RECOMMENDATION")
    _print_model(recommendation)

    _print_header("DONE")
    print("Sample Market Data -> IndicatorSnapshot -> MarketContext ->")
    print("TradingConditions -> StrategyEvaluation -> RiskAssessment ->")
    print("TradeRecommendation")


if __name__ == "__main__":
    main()
