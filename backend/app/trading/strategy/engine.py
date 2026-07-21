"""
Executes every registered strategy against the same inputs and returns
their evaluations. Does not compare, rank, or choose between them -
that is explicitly out of scope for this phase.
"""

from app.trading.conditions.models import TradingConditions
from app.trading.context.models import MarketContext
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.strategy.models import StrategyEvaluation
from app.trading.strategy.registry import StrategyRegistry


def run_strategies(
    registry: StrategyRegistry,
    snapshot: IndicatorSnapshot,
    context: MarketContext,
    conditions: TradingConditions,
) -> list[StrategyEvaluation]:
    return [
        strategy.evaluate(snapshot, context, conditions) for strategy in registry.all()
    ]
