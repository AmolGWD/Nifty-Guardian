from app.runtime.engine_config import EngineConfig
from app.runtime.market_data_source import StaticListSource
from app.runtime.session_controller import SessionState
from app.runtime.shutdown import shutdown_runtime
from app.runtime.startup import start_runtime
from tests.runtime.helpers import build_candles


def test_shutdown_ends_a_running_session() -> None:
    context = start_runtime(
        config=EngineConfig(), market_data_source=StaticListSource(build_candles(30))
    )
    context.engine.run()  # auto-stops on completion by default -> STOPPED

    summary = shutdown_runtime(context)

    assert context.session_controller.state == SessionState.ENDED
    assert summary.final_health.current_state == SessionState.ENDED


def test_shutdown_ends_a_paused_session() -> None:
    context = start_runtime(
        config=EngineConfig(auto_stop_on_completion=False, maximum_candles=10),
        market_data_source=StaticListSource(build_candles(30)),
    )
    context.engine.run()
    context.session_controller.pause()

    summary = shutdown_runtime(context)

    assert context.session_controller.state == SessionState.ENDED
    assert summary.final_health.processed_candles == 10


def test_shutdown_is_idempotent_when_already_ended() -> None:
    context = start_runtime(
        config=EngineConfig(), market_data_source=StaticListSource(build_candles(5))
    )
    context.engine.run()
    shutdown_runtime(context)
    assert context.session_controller.state == SessionState.ENDED

    # Calling shutdown again must not raise even though the session is
    # already ENDED - stop()/end_session() are only invoked from
    # RUNNING/PAUSED and STOPPED respectively.
    summary = shutdown_runtime(context)
    assert summary.final_health.current_state == SessionState.ENDED


def test_summary_journal_reflects_entries_recorded_during_the_run() -> None:
    context = start_runtime(
        config=EngineConfig(), market_data_source=StaticListSource(build_candles(30))
    )
    context.engine.run()

    entries_before_shutdown = len(context.execution_journal.all_entries())
    summary = shutdown_runtime(context)

    # shutdown_runtime reads the journal before its own final snapshots
    # (which themselves append a couple more entries) - so the summary's
    # count reflects the run, not shutdown's own bookkeeping.
    all_entries = context.execution_journal.all_entries()
    assert len(summary.journaled_entries) == entries_before_shutdown
    assert summary.journaled_entries == all_entries[:entries_before_shutdown]


def test_summary_portfolio_and_performance_are_final_snapshots() -> None:
    context = start_runtime(
        config=EngineConfig(), market_data_source=StaticListSource(build_candles(30))
    )
    context.engine.run()

    summary = shutdown_runtime(context)

    assert summary.final_portfolio.cash == context.portfolio_manager.snapshot().cash
    assert (
        summary.final_performance.orders_submitted
        == context.performance_monitor.snapshot().orders_submitted
    )
