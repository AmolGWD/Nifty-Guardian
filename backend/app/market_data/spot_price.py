"""
Live spot price for an underlying index/instrument.
"""

from datetime import datetime

from app.market_data.client import MarketDataClient
from app.market_data.schemas import SpotPrice

NIFTY_50_SYMBOL = "NSE:NIFTY 50"


class SpotPriceService:
    def get_spot_price(self, client: MarketDataClient, symbol: str = NIFTY_50_SYMBOL) -> SpotPrice:
        quote = client.get_ltp([symbol])[symbol]

        return SpotPrice(
            symbol=symbol,
            price=float(quote["last_price"]),
            as_of=datetime.now(),
        )


spot_price_service = SpotPriceService()
