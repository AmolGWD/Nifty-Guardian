from app.market_data.market_session import MarketSessionStatus
from app.trading.conditions.market_open_filter import is_market_open


def test_market_open_when_session_is_open() -> None:
    assert is_market_open(MarketSessionStatus.OPEN) is True


def test_market_not_open_when_pre_market() -> None:
    assert is_market_open(MarketSessionStatus.PRE_MARKET) is False


def test_market_not_open_when_closed() -> None:
    assert is_market_open(MarketSessionStatus.CLOSED) is False
