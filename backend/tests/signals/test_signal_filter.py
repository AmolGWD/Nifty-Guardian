from datetime import datetime
from typing import Any

from app.signals.models import GuardianScore, SignalConfig
from app.signals.signal_filter import SignalFilter
from app.trading.strategy.models import StrategyStrength

_MARKET_HOURS = datetime(2026, 1, 5, 10, 0)  # a Monday, well within 09:15-15:30
_OUTSIDE_HOURS = datetime(2026, 1, 5, 20, 0)


def _score(score: float = 90.0) -> GuardianScore:
    return GuardianScore(
        score=score, strength=StrategyStrength.STRONG, reward_risk_ratio=2.0, reasons=["r"]
    )


def _filter(**overrides: Any) -> SignalFilter:
    return SignalFilter(config=SignalConfig(_env_file=None, **overrides))


def test_allows_a_high_confidence_signal_within_trading_hours() -> None:
    decision = _filter().should_emit(
        strategy_name="EMABreakout", guardian_score=_score(90.0), now=_MARKET_HOURS
    )
    assert decision.allowed is True


def test_rejects_outside_trading_hours() -> None:
    decision = _filter().should_emit(
        strategy_name="EMABreakout", guardian_score=_score(90.0), now=_OUTSIDE_HOURS
    )
    assert decision.allowed is False
    assert "trading hours" in decision.reason


def test_rejects_below_confidence_threshold() -> None:
    decision = _filter(confidence_threshold=80.0).should_emit(
        strategy_name="EMABreakout", guardian_score=_score(50.0), now=_MARKET_HOURS
    )
    assert decision.allowed is False
    assert "below threshold" in decision.reason


def test_rejects_within_cooldown_of_last_signal() -> None:
    signal_filter = _filter(cooldown_minutes=15.0)
    signal_filter.record_emitted(strategy_name="EMABreakout", now=_MARKET_HOURS)

    decision = signal_filter.should_emit(
        strategy_name="EMABreakout",
        guardian_score=_score(90.0),
        now=_MARKET_HOURS.replace(minute=10),  # 10 minutes later, cooldown 15
    )

    assert decision.allowed is False
    assert "cooldown" in decision.reason


def test_allows_again_once_cooldown_elapses() -> None:
    signal_filter = _filter(cooldown_minutes=15.0)
    signal_filter.record_emitted(strategy_name="EMABreakout", now=_MARKET_HOURS)

    decision = signal_filter.should_emit(
        strategy_name="EMABreakout",
        guardian_score=_score(90.0),
        now=_MARKET_HOURS.replace(minute=30),  # 20 minutes later
    )

    assert decision.allowed is True


def test_cooldown_is_tracked_independently_per_strategy() -> None:
    signal_filter = _filter(cooldown_minutes=15.0)
    signal_filter.record_emitted(strategy_name="StrategyA", now=_MARKET_HOURS)

    decision = signal_filter.should_emit(
        strategy_name="StrategyB", guardian_score=_score(90.0), now=_MARKET_HOURS
    )

    assert decision.allowed is True


def test_rejects_once_max_signals_per_day_reached() -> None:
    signal_filter = _filter(max_signals_per_day=2, cooldown_minutes=0.0)
    signal_filter.record_emitted(strategy_name="EMABreakout", now=_MARKET_HOURS)
    signal_filter.record_emitted(strategy_name="EMABreakout", now=_MARKET_HOURS)

    decision = signal_filter.should_emit(
        strategy_name="EMABreakout", guardian_score=_score(90.0), now=_MARKET_HOURS
    )

    assert decision.allowed is False
    assert "max" in decision.reason


def test_daily_count_resets_on_a_new_day() -> None:
    signal_filter = _filter(max_signals_per_day=1, cooldown_minutes=0.0)
    signal_filter.record_emitted(strategy_name="EMABreakout", now=_MARKET_HOURS)

    next_day = _MARKET_HOURS.replace(day=6)
    decision = signal_filter.should_emit(
        strategy_name="EMABreakout", guardian_score=_score(90.0), now=next_day
    )

    assert decision.allowed is True
    assert signal_filter.signals_sent_today == 0
