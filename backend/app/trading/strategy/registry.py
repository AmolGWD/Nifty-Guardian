"""
Plugin registry: strategies register themselves here, and the Strategy
Engine runs whatever is registered without knowing about any concrete
strategy class.
"""

from app.trading.strategy.base import Strategy
from app.trading.strategy.ema_breakout import EMABreakoutStrategy


class StrategyRegistry:
    def __init__(self) -> None:
        self._strategies: list[Strategy] = []

    def register(self, strategy: Strategy) -> None:
        self._strategies.append(strategy)

    def all(self) -> tuple[Strategy, ...]:
        return tuple(self._strategies)


def default_registry() -> StrategyRegistry:
    """A registry pre-populated with every built-in strategy."""
    registry = StrategyRegistry()
    registry.register(EMABreakoutStrategy())
    return registry
