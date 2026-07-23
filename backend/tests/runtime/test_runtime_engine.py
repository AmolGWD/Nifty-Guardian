from app.runtime.engine_config import EngineConfig, ReplaySpeed
from app.runtime.market_data_source import StaticListSource
from app.runtime.session_controller import SessionState
from app.runtime.startup import start_runtime
from app.trading.strategy.models import StrategyDirection
from tests.runtime.helpers import build_candles


def _fast_config(**overrides: object) -> EngineConfig:
    base: dict[str, object] = dict(replay_speed=ReplaySpeed.UNLIMITED)
    base.update(overrides)
    return EngineConfig(**base)


def test_run_processes_every_candle_and_ends_session_on_completion() -> None:
    candles = build_candles(60)
    context = start_runtime(config=_fast_config(), market_data_source=StaticListSource(candles))

    context.engine.run()

    assert context.engine.processed_count == 60
    assert context.session_controller.state == SessionState.STOPPED


def test_a_bearish_downtrend_opens_a_short_position_end_to_end() -> None:
    candles = build_candles(40, direction="down")
    context = start_runtime(config=_fast_config(), market_data_source=StaticListSource(candles))

    context.engine.run()

    positions = list(context.position_manager.open_positions()) + list(
        context.position_manager.closed_positions()
    )
    assert len(positions) >= 1
    assert positions[0].direction == StrategyDirection.SHORT


def test_maximum_candles_halts_processing_at_the_limit() -> None:
    candles = build_candles(60)
    config = _fast_config(maximum_candles=10)
    context = start_runtime(config=config, market_data_source=StaticListSource(candles))

    context.engine.run()

    assert context.engine.processed_count == 10


def test_auto_stop_on_completion_false_leaves_session_running() -> None:
    candles = build_candles(60)
    config = _fast_config(maximum_candles=10, auto_stop_on_completion=False)
    context = start_runtime(config=config, market_data_source=StaticListSource(candles))

    context.engine.run()

    assert context.engine.processed_count == 10
    assert context.session_controller.state == SessionState.RUNNING


def test_run_starts_the_session_from_not_started() -> None:
    candles = build_candles(5)
    context = start_runtime(config=_fast_config(), market_data_source=StaticListSource(candles))

    assert context.session_controller.state == SessionState.NOT_STARTED
    context.engine.run()
    assert context.session_controller.state in (SessionState.STOPPED, SessionState.RUNNING)


def test_pause_mid_stream_halts_further_processing_until_resumed() -> None:
    candles = build_candles(60)
    context = start_runtime(config=_fast_config(), market_data_source=StaticListSource(candles))

    calls = {"n": 0}
    original = context.event_processor.process_candle

    def counting_process(candle: object, history: object) -> float:
        calls["n"] += 1
        if calls["n"] == 15:
            context.session_controller.pause()
        return original(candle, history)  # type: ignore[arg-type]

    context.event_processor.process_candle = counting_process  # type: ignore[method-assign]

    context.engine.run()
    state_after_pause = context.session_controller.state
    assert context.engine.processed_count == 15
    assert state_after_pause == SessionState.PAUSED

    context.session_controller.resume()
    context.engine.run()
    state_after_completion = context.session_controller.state
    assert context.engine.processed_count == 60
    assert state_after_completion == SessionState.STOPPED


def test_run_is_a_no_op_once_ended() -> None:
    candles = build_candles(5)
    context = start_runtime(config=_fast_config(), market_data_source=StaticListSource(candles))

    context.engine.run()
    context.session_controller.end_session()

    context.engine.run()  # must not raise, must not resume/restart
    assert context.session_controller.state == SessionState.ENDED
    assert context.engine.processed_count == 5


def test_replay_produces_identical_results_for_the_same_inputs() -> None:
    config = _fast_config(random_seed=42)

    candles_a = build_candles(80)
    context_a = start_runtime(config=config, market_data_source=StaticListSource(candles_a))
    context_a.engine.run()
    portfolio_a = context_a.portfolio_manager.snapshot()

    candles_b = build_candles(80)
    context_b = start_runtime(config=config, market_data_source=StaticListSource(candles_b))
    context_b.engine.run()
    portfolio_b = context_b.portfolio_manager.snapshot()

    assert context_a.engine.processed_count == context_b.engine.processed_count
    assert portfolio_a.total_equity == portfolio_b.total_equity
    assert len(context_a.order_manager.all_orders()) == len(context_b.order_manager.all_orders())


def test_health_monitor_reflects_engine_progress() -> None:
    candles = build_candles(30)
    context = start_runtime(config=_fast_config(), market_data_source=StaticListSource(candles))

    context.engine.run()

    health = context.health_monitor.snapshot()
    assert health.processed_candles == 30
    assert health.average_processing_latency_seconds is not None
    assert health.average_processing_latency_seconds >= 0.0
