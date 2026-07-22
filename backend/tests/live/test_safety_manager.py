from datetime import time as time_of_day
from typing import Any

from app.live.models import LiveConfig
from app.live.safety_manager import SafetyManager


def _config(**overrides: Any) -> LiveConfig:
    return LiveConfig(_env_file=None, **overrides)


def test_all_gates_pass_by_default() -> None:
    manager = SafetyManager(_config())
    decision = manager.check_before_order(time_of_day(10, 0))
    assert decision.allowed is True
    assert decision.gate == "all_gates"


def test_emergency_stop_overrides_every_other_gate() -> None:
    manager = SafetyManager(_config())
    manager.trigger_emergency_stop("operator request")

    decision = manager.check_before_order(time_of_day(10, 0))

    assert decision.allowed is False
    assert decision.gate == "emergency_stop"
    assert manager.is_emergency_stopped


def test_kill_switch_blocks_orders_until_disengaged() -> None:
    manager = SafetyManager(_config())
    manager.engage_kill_switch("manual halt")

    assert manager.check_before_order(time_of_day(10, 0)).gate == "kill_switch"

    manager.disengage_kill_switch()

    assert manager.check_before_order(time_of_day(10, 0)).gate == "all_gates"


def test_circuit_breaker_trips_after_consecutive_failures() -> None:
    manager = SafetyManager(_config(), circuit_breaker_threshold=3)
    for _ in range(3):
        manager.record_order_outcome(succeeded=False)

    decision = manager.check_before_order(time_of_day(10, 0))

    assert decision.gate == "circuit_breaker"


def test_circuit_breaker_resets_on_a_success() -> None:
    manager = SafetyManager(_config(), circuit_breaker_threshold=2)
    manager.record_order_outcome(succeeded=False)
    manager.record_order_outcome(succeeded=True)
    manager.record_order_outcome(succeeded=False)

    decision = manager.check_before_order(time_of_day(10, 0))

    assert decision.gate == "all_gates"


def test_trading_hours_gate_rejects_outside_configured_window() -> None:
    manager = SafetyManager(_config(trading_start="09:15", trading_end="15:30"))

    assert manager.check_before_order(time_of_day(8, 0)).gate == "trading_hours"
    assert manager.check_before_order(time_of_day(16, 0)).gate == "trading_hours"
    assert manager.check_before_order(time_of_day(12, 0)).gate == "all_gates"


def test_max_orders_per_day_gate() -> None:
    manager = SafetyManager(_config(max_orders_per_day=2))
    manager.record_order_submitted()
    manager.record_order_submitted()

    decision = manager.check_before_order(time_of_day(10, 0))

    assert decision.gate == "max_orders_per_day"


def test_max_daily_loss_gate_only_counts_losses() -> None:
    manager = SafetyManager(_config(max_daily_loss=500.0))
    manager.record_realized_pnl(1000.0)  # a gain never counts against the loss cap
    assert manager.check_before_order(time_of_day(10, 0)).gate == "all_gates"

    manager.record_realized_pnl(-600.0)

    assert manager.check_before_order(time_of_day(10, 0)).gate == "max_daily_loss"


def test_max_open_positions_gate() -> None:
    manager = SafetyManager(_config(max_open_positions=1))
    manager.record_position_opened()

    decision = manager.check_before_order(time_of_day(10, 0))

    assert decision.gate == "max_open_positions"

    manager.record_position_closed()

    assert manager.check_before_order(time_of_day(10, 0)).gate == "all_gates"


def test_reset_daily_counters_clears_order_count_and_loss() -> None:
    manager = SafetyManager(_config(max_orders_per_day=1, max_daily_loss=100.0))
    manager.record_order_submitted()
    manager.record_realized_pnl(-200.0)

    manager.reset_daily_counters()

    assert manager.check_before_order(time_of_day(10, 0)).gate == "all_gates"


def test_every_decision_is_recorded_in_order() -> None:
    manager = SafetyManager(_config())
    manager.check_before_order(time_of_day(10, 0))
    manager.engage_kill_switch("halt")
    manager.check_before_order(time_of_day(10, 0))

    assert [d.gate for d in manager.decisions] == ["all_gates", "kill_switch", "kill_switch"]
