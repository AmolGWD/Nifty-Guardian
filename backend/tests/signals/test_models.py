from datetime import datetime
from typing import Any

import pytest

from app.signals.models import DummyTrade, ExitReason, GuardianScore, SignalConfig
from app.trading.strategy.models import StrategyDirection, StrategyStrength


def _config(**overrides: Any) -> SignalConfig:
    return SignalConfig(_env_file=None, **overrides)


def _score(**overrides: object) -> GuardianScore:
    base: dict[str, object] = dict(
        score=80.0, strength=StrategyStrength.STRONG, reward_risk_ratio=2.0, reasons=["a reason"]
    )
    base.update(overrides)
    return GuardianScore(**base)


def test_guardian_score_rejects_out_of_range_score() -> None:
    with pytest.raises(ValueError):
        _score(score=101.0)
    with pytest.raises(ValueError):
        _score(score=-1.0)


def test_dummy_trade_close_computes_pnl_derived_fields() -> None:
    trade = DummyTrade(
        trade_id="t1",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        guardian_score=_score(),
        entry_price=100.0,
        stop_loss=95.0,
        target=115.0,
        quantity=10,
        opened_at=datetime(2026, 1, 5, 9, 30),
    )

    closed = trade.close(
        exit_price=115.0,
        closed_at=datetime(2026, 1, 5, 11, 0),
        pnl=150.0,
        exit_reason=ExitReason.TARGET,
    )

    assert closed.status.value == "Closed"
    assert closed.exit_price == 115.0
    assert closed.pnl == 150.0
    assert closed.r_multiple == pytest.approx(3.0)  # 15 pnl/unit / 5 risk/unit
    assert closed.duration_seconds == pytest.approx(3600 * 1.5)
    assert closed.exit_reason == ExitReason.TARGET


def test_dummy_trade_close_handles_zero_risk_gracefully() -> None:
    trade = DummyTrade(
        trade_id="t2",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        guardian_score=_score(),
        entry_price=100.0,
        stop_loss=100.0,  # zero risk-per-unit
        target=115.0,
        quantity=10,
        opened_at=datetime(2026, 1, 5, 9, 30),
    )

    closed = trade.close(
        exit_price=115.0,
        closed_at=datetime(2026, 1, 5, 11, 0),
        pnl=150.0,
        exit_reason=ExitReason.TARGET,
    )

    assert closed.r_multiple == 0.0


def test_signal_config_defaults() -> None:
    config = _config()
    assert config.confidence_threshold == 65.0
    assert config.cooldown_minutes == 15.0
    assert config.max_signals_per_day == 5


@pytest.mark.parametrize(
    "field,value",
    [
        ("confidence_threshold", -1.0),
        ("confidence_threshold", 101.0),
        ("cooldown_minutes", -1.0),
        ("max_signals_per_day", 0),
    ],
)
def test_signal_config_rejects_invalid_values(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        _config(**{field: value})
