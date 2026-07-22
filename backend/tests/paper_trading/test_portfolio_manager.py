import pytest

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import PortfolioUpdatedEvent
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager
from app.trading.strategy.models import StrategyDirection


def test_initial_snapshot_matches_initial_cash() -> None:
    bus = EventBus()
    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )

    portfolio = portfolio_manager.snapshot()

    assert portfolio.cash == 100_000.0
    assert portfolio.total_equity == 100_000.0
    assert portfolio.available_margin == 100_000.0
    assert portfolio.open_position_ids == ()
    assert portfolio.closed_position_ids == ()


def test_total_equity_includes_unrealized_pnl_of_open_positions() -> None:
    bus = EventBus()
    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )

    position = position_manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    position_manager.update_unrealized_pnl(position.position_id, 105.0)

    portfolio = portfolio_manager.snapshot()

    assert portfolio.total_equity == pytest.approx(100_050.0)
    assert portfolio.open_position_ids == (position.position_id,)


def test_record_cash_change_updates_cash_and_daily_pnl() -> None:
    bus = EventBus()
    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )

    portfolio_manager.record_cash_change(500.0)
    portfolio_manager.record_cash_change(-200.0)

    portfolio = portfolio_manager.snapshot()
    assert portfolio.cash == pytest.approx(100_300.0)
    assert portfolio.daily_pnl == pytest.approx(300.0)


def test_reset_daily_pnl_does_not_affect_cash() -> None:
    bus = EventBus()
    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )

    portfolio_manager.record_cash_change(500.0)
    portfolio_manager.reset_daily_pnl()

    portfolio = portfolio_manager.snapshot()
    assert portfolio.cash == pytest.approx(100_500.0)
    assert portfolio.daily_pnl == 0.0


def test_drawdown_reflects_decline_from_peak_equity() -> None:
    bus = EventBus()
    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )

    position = position_manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    position_manager.update_unrealized_pnl(position.position_id, 110.0)
    portfolio_manager.snapshot()  # peak becomes 100_100

    position_manager.update_unrealized_pnl(position.position_id, 95.0)
    portfolio = portfolio_manager.snapshot()

    assert portfolio.peak_equity == pytest.approx(100_100.0)
    assert portfolio.drawdown == pytest.approx(150.0)


def test_snapshot_publishes_portfolio_updated() -> None:
    bus = EventBus()
    published: list[PortfolioUpdatedEvent] = []
    bus.subscribe(PortfolioUpdatedEvent, published.append)

    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )
    portfolio_manager.snapshot()

    assert len(published) == 1


def test_closed_positions_are_excluded_from_equity_but_tracked() -> None:
    bus = EventBus()
    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )

    position = position_manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    position_manager.exit(position.position_id, exit_quantity=10, exit_price=110.0)
    portfolio_manager.record_cash_change(100.0)

    portfolio = portfolio_manager.snapshot()

    assert portfolio.closed_position_ids == (position.position_id,)
    assert portfolio.open_position_ids == ()
    assert portfolio.total_equity == pytest.approx(100_100.0)
