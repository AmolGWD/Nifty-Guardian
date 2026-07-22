from app.runtime.engine_config import EngineConfig
from app.runtime.market_data_source import StaticListSource
from app.runtime.session_controller import SessionState
from app.runtime.startup import start_runtime
from app.trading.risk.models import RiskConfig
from app.trading.strategy.registry import default_registry
from tests.runtime.helpers import build_candles


def test_start_runtime_wires_every_component() -> None:
    context = start_runtime(
        config=EngineConfig(), market_data_source=StaticListSource(build_candles(5))
    )

    assert context.event_bus is not None
    assert context.order_manager is not None
    assert context.position_manager is not None
    assert context.portfolio_manager is not None
    assert context.broker is not None
    assert context.execution_journal is not None
    assert context.performance_monitor is not None
    assert context.health_monitor is not None
    assert context.session_controller is not None
    assert context.event_processor is not None
    assert context.engine is not None


def test_session_starts_not_started() -> None:
    context = start_runtime(
        config=EngineConfig(), market_data_source=StaticListSource(build_candles(5))
    )
    assert context.session_controller.state == SessionState.NOT_STARTED


def test_default_initial_capital_reflected_in_portfolio() -> None:
    context = start_runtime(
        config=EngineConfig(), market_data_source=StaticListSource(build_candles(5))
    )
    assert context.portfolio_manager.snapshot().cash == 100_000.0


def test_custom_initial_capital_is_respected() -> None:
    context = start_runtime(
        config=EngineConfig(),
        market_data_source=StaticListSource(build_candles(5)),
        initial_capital=250_000.0,
    )
    assert context.portfolio_manager.snapshot().cash == 250_000.0


def test_defaults_risk_config_and_strategy_registry_when_omitted() -> None:
    context = start_runtime(
        config=EngineConfig(), market_data_source=StaticListSource(build_candles(5))
    )
    # No exception constructing/running with defaulted collaborators.
    context.engine.run()
    assert context.engine.processed_count == 5


def test_accepts_explicit_risk_config_and_strategy_registry() -> None:
    context = start_runtime(
        config=EngineConfig(),
        market_data_source=StaticListSource(build_candles(5)),
        risk_config=RiskConfig(),
        strategy_registry=default_registry(),
    )
    assert context.engine.processed_count == 0
    context.engine.run()
    assert context.engine.processed_count == 5


def test_execution_journal_is_already_subscribed_to_the_event_bus() -> None:
    context = start_runtime(
        config=EngineConfig(), market_data_source=StaticListSource(build_candles(30))
    )
    context.engine.run()
    assert len(context.execution_journal.all_entries()) > 0
