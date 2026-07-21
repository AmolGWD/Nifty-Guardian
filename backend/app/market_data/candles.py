"""
Historical OHLCV candle data.
"""

from datetime import datetime

from app.market_data.client import MarketDataClient
from app.market_data.schemas import Candle


class CandleService:
    def get_candles(
        self,
        client: MarketDataClient,
        instrument_token: int,
        from_date: datetime,
        to_date: datetime,
        interval: str,
    ) -> list[Candle]:
        raw_candles = client.get_historical_data(instrument_token, from_date, to_date, interval)

        return [
            Candle(
                timestamp=row["date"],
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]),
            )
            for row in raw_candles
        ]


candle_service = CandleService()
