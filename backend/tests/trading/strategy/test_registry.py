from app.trading.conditions.models import TradingConditions
from app.trading.context.models import MarketContext
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.strategy.ema_breakout import EMABreakoutStrategy
from app.trading.strategy.models import StrategyEvaluation
from app.trading.strategy.registry import StrategyRegistry, default_registry


class _FakeStrategy:
    name = "Fake"

    def evaluate(
        self,
        snapshot: IndicatorSnapshot,
        context: MarketContext,
        conditions: TradingConditions,
    ) -> StrategyEvaluation:
        raise NotImplementedError


def test_empty_registry_has_no_strategies() -> None:
    registry = StrategyRegistry()

    assert registry.all() == ()


def test_register_adds_a_strategy() -> None:
    registry = StrategyRegistry()
    strategy = _FakeStrategy()

    registry.register(strategy)

    assert registry.all() == (strategy,)


def test_default_registry_includes_ema_breakout() -> None:
    registry = default_registry()

    strategies = registry.all()

    assert len(strategies) == 1
    assert isinstance(strategies[0], EMABreakoutStrategy)
    assert strategies[0].name == "EMABreakout"
