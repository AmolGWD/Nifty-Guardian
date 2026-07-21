from app.trading.conditions.models import TradingConditions
from app.trading.context.models import MarketContext
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.strategy.engine import run_strategies
from app.trading.strategy.models import (
    StrategyDirection,
    StrategyEvaluation,
    StrategyStrength,
)
from app.trading.strategy.registry import StrategyRegistry, default_registry
from tests.trading.conditions.helpers import make_market_context
from tests.trading.context.helpers import make_snapshot
from tests.trading.strategy.helpers import make_trading_conditions


class _StubStrategy:
    def __init__(self, name: str) -> None:
        self.name = name

    def evaluate(
        self,
        snapshot: IndicatorSnapshot,
        context: MarketContext,
        conditions: TradingConditions,
    ) -> StrategyEvaluation:
        return StrategyEvaluation(
            strategy_name=self.name,
            valid=False,
            direction=StrategyDirection.NONE,
            strength=StrategyStrength.WEAK,
            reasons=[],
            warnings=[],
        )


def test_run_strategies_with_default_registry_returns_one_evaluation() -> None:
    registry = default_registry()

    evaluations = run_strategies(
        registry, make_snapshot(), make_market_context(), make_trading_conditions()
    )

    assert len(evaluations) == 1
    assert evaluations[0].strategy_name == "EMABreakout"


def test_run_strategies_executes_every_registered_strategy_in_order() -> None:
    registry = StrategyRegistry()
    registry.register(_StubStrategy("First"))
    registry.register(_StubStrategy("Second"))

    evaluations = run_strategies(
        registry, make_snapshot(), make_market_context(), make_trading_conditions()
    )

    assert [evaluation.strategy_name for evaluation in evaluations] == ["First", "Second"]


def test_run_strategies_returns_empty_list_for_empty_registry() -> None:
    registry = StrategyRegistry()

    evaluations = run_strategies(
        registry, make_snapshot(), make_market_context(), make_trading_conditions()
    )

    assert evaluations == []
