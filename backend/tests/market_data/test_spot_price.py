from app.market_data.spot_price import NIFTY_50_SYMBOL, SpotPriceService
from tests.market_data.fakes import FakeMarketDataClient


def test_get_spot_price_returns_normalized_price() -> None:
    client = FakeMarketDataClient(
        ltp_responses={NIFTY_50_SYMBOL: {"instrument_token": 256265, "last_price": 24820.5}}
    )
    service = SpotPriceService()

    spot = service.get_spot_price(client)

    assert spot.symbol == NIFTY_50_SYMBOL
    assert spot.price == 24820.5


def test_get_spot_price_accepts_custom_symbol() -> None:
    client = FakeMarketDataClient(
        ltp_responses={"NSE:BANKNIFTY": {"instrument_token": 1, "last_price": 51000.0}}
    )
    service = SpotPriceService()

    spot = service.get_spot_price(client, symbol="NSE:BANKNIFTY")

    assert spot.symbol == "NSE:BANKNIFTY"
    assert spot.price == 51000.0
