import os
from pathlib import Path

from dotenv import load_dotenv
from kiteconnect import KiteConnect

from app.auth.token_store import token_store
from app.market.providers.base_provider import BaseMarketProvider

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")


class KiteProvider(BaseMarketProvider):

    def __init__(self):

        self.api_key = os.getenv("KITE_API_KEY")

        if not self.api_key:
            raise Exception("KITE_API_KEY not found in .env")

        self.kite = KiteConnect(api_key=self.api_key)

    def get_market_data(self):

        access_token = token_store.access_token()

        if not access_token:
            raise Exception("Kite access token not found. Please login again.")

        self.kite.set_access_token(access_token)

        quote = self.kite.quote(["NSE:NIFTY 50"])

        data = quote["NSE:NIFTY 50"]

        ohlc = data["ohlc"]

        last_price = float(data["last_price"])
        previous_close = float(ohlc["close"])

        change = round(last_price - previous_close, 2)

        market_mood = "Bullish" if change >= 0 else "Bearish"

        trend = "Uptrend" if change >= 0 else "Downtrend"

        return {

            "symbol": "NIFTY 50",

            "price": last_price,

            "change": change,

            "open": float(ohlc["open"]),

            "high": float(ohlc["high"]),

            "low": float(ohlc["low"]),

            "previous_close": previous_close,

            "market_mood": market_mood,

            "trend": trend,

            "volatility": "Live",

            "pcr": 0.0,

            "oi_bias": "Waiting",

            "last_refresh": data["timestamp"].strftime("%H:%M:%S")

        }


kite_provider = KiteProvider()