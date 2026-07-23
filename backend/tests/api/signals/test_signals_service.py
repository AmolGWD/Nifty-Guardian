import time

import pytest

from app.api.signals.signals_service import SignalEngineConflictError, SignalEngineRuntimeService
from app.notifications.models import TelegramStatus


def test_status_before_start_reports_not_running(fresh_service: SignalEngineRuntimeService) -> None:
    status = fresh_service.status()
    assert status.running is False
    assert status.live_session_state is None


def test_state_before_start_is_an_honest_empty_snapshot(
    fresh_service: SignalEngineRuntimeService,
) -> None:
    state = fresh_service.state()
    assert state.market_status is None
    assert state.market_bias.value == "None"
    assert state.latest_signal_type is None
    assert state.latest_entry_price is None
    assert state.latest_stop_loss is None
    assert state.latest_target is None
    assert state.telegram_status is None
    assert state.signals_sent_today == 0


def test_performance_before_start_is_all_zeros(fresh_service: SignalEngineRuntimeService) -> None:
    performance = fresh_service.performance()
    assert performance.open_trades == []
    assert performance.closed_trades == []
    assert performance.win_rate == 0.0


def test_trades_before_start_is_empty(fresh_service: SignalEngineRuntimeService) -> None:
    assert fresh_service.trades() == []


def test_report_today_before_start_is_zeroed(fresh_service: SignalEngineRuntimeService) -> None:
    report = fresh_service.report_today()
    assert report.total_signals == 0
    assert report.best_trade is None


def test_start_transitions_to_running_and_produces_trades(
    fresh_service: SignalEngineRuntimeService,
) -> None:
    status = fresh_service.start()
    assert status.running is True

    time.sleep(1.0)

    assert len(fresh_service.trades()) > 0
    fresh_service.stop()


def test_state_reflects_a_live_signal_after_running(
    fresh_service: SignalEngineRuntimeService,
) -> None:
    fresh_service.start()
    time.sleep(1.0)

    state = fresh_service.state()
    assert state.market_status is not None
    assert state.latest_signal_type is not None
    assert state.latest_entry_price is not None
    assert state.latest_stop_loss is not None
    assert state.latest_target is not None
    # TELEGRAM_ENABLED defaults to false in this test environment, so no
    # send is ever attempted - telegram_status honestly stays None rather
    # than fabricating a status for a disabled feature.
    assert state.telegram_status is None
    fresh_service.stop()


def test_state_reflects_the_notification_services_own_last_status(
    fresh_service: SignalEngineRuntimeService,
) -> None:
    fresh_service.start()
    assert fresh_service._notification_service is not None
    fresh_service._notification_service.last_status = TelegramStatus.SENT

    assert fresh_service.state().telegram_status == TelegramStatus.SENT
    fresh_service.stop()


def test_starting_twice_raises_a_conflict_error(fresh_service: SignalEngineRuntimeService) -> None:
    fresh_service.start()
    with pytest.raises(SignalEngineConflictError):
        fresh_service.start()
    fresh_service.stop()


def test_stopping_without_starting_raises_a_conflict_error(
    fresh_service: SignalEngineRuntimeService,
) -> None:
    with pytest.raises(SignalEngineConflictError):
        fresh_service.stop()


def test_stop_transitions_back_to_not_running(fresh_service: SignalEngineRuntimeService) -> None:
    fresh_service.start()
    status = fresh_service.stop()
    assert status.running is False


def test_performance_reflects_real_trades_after_running(
    fresh_service: SignalEngineRuntimeService,
) -> None:
    fresh_service.start()
    time.sleep(1.0)

    performance = fresh_service.performance()
    assert len(performance.closed_trades) + len(performance.open_trades) > 0
    fresh_service.stop()
