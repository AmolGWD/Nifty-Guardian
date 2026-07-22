from app.runtime.engine_config import EngineConfig, ReplaySpeed
from app.runtime.market_data_source import StaticListSource
from app.runtime.replay import run_replay
from app.runtime.session_controller import SessionState
from tests.runtime.helpers import build_candles


def test_run_replay_returns_context_and_summary() -> None:
    candles = build_candles(40)
    context, summary = run_replay(
        market_data_source=StaticListSource(candles),
        config=EngineConfig(replay_speed=ReplaySpeed.UNLIMITED),
    )

    assert context.engine.processed_count == 40
    assert context.session_controller.state == SessionState.ENDED
    assert summary.final_health.processed_candles == 40


def test_run_replay_is_deterministic_for_the_same_seed() -> None:
    config = EngineConfig(replay_speed=ReplaySpeed.UNLIMITED, random_seed=7)

    _, summary_a = run_replay(
        market_data_source=StaticListSource(build_candles(80)), config=config
    )
    _, summary_b = run_replay(
        market_data_source=StaticListSource(build_candles(80)), config=config
    )

    assert summary_a.final_portfolio.total_equity == summary_b.final_portfolio.total_equity
    assert (
        summary_a.final_performance.orders_submitted
        == summary_b.final_performance.orders_submitted
    )
    assert summary_a.final_health.processed_candles == summary_b.final_health.processed_candles


def test_run_replay_respects_maximum_candles() -> None:
    context, summary = run_replay(
        market_data_source=StaticListSource(build_candles(50)),
        config=EngineConfig(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=12),
    )
    assert context.engine.processed_count == 12
    assert summary.final_health.processed_candles == 12
