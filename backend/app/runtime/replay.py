"""
Deterministic replay: wires startup -> run -> shutdown into a single
call. Determinism here means what it means for every other replay-like
component in this codebase (Grid Search, Walk-Forward, Monte Carlo):
the same inputs (candles, config) always produce the same sequence of
events and the same final state - `EngineConfig.random_seed` is
reserved for that guarantee if a future perturbation ever needs real
randomness (this phase's pipeline is entirely deterministic on its
own - Indicators/Context/Conditions/Strategy/Risk/Decision never draw
from an RNG - so the seed is not yet exercised by anything; this is an
honest placeholder, not a claim that randomness is used today).
"""

from app.runtime.engine_config import EngineConfig
from app.runtime.market_data_source import MarketDataSource
from app.runtime.shutdown import ShutdownSummary, shutdown_runtime
from app.runtime.startup import RuntimeContext, start_runtime
from app.trading.risk.models import RiskConfig
from app.trading.strategy.registry import StrategyRegistry


def run_replay(
    *,
    market_data_source: MarketDataSource,
    config: EngineConfig,
    initial_capital: float = 100_000.0,
    risk_config: RiskConfig | None = None,
    strategy_registry: StrategyRegistry | None = None,
    warmup_candles: int = 20,
) -> tuple[RuntimeContext, ShutdownSummary]:
    context = start_runtime(
        config=config,
        market_data_source=market_data_source,
        initial_capital=initial_capital,
        risk_config=risk_config,
        strategy_registry=strategy_registry,
        warmup_candles=warmup_candles,
    )
    context.engine.run()
    summary = shutdown_runtime(context)
    return context, summary
