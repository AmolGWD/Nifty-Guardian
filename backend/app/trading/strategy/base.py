"""
Common interface every strategy plugin implements. The Strategy Engine
(engine.py) runs every registered Strategy against the same three
inputs and collects their evaluations - it does not compare, rank, or
choose between them (that is later work, not this phase).
"""

from typing import Protocol

from app.trading.conditions.models import TradingConditions
from app.trading.context.models import MarketContext
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.strategy.models import StrategyEvaluation


class Strategy(Protocol):
    name: str

    def evaluate(
        self,
        snapshot: IndicatorSnapshot,
        context: MarketContext,
        conditions: TradingConditions,
    ) -> StrategyEvaluation: ...
