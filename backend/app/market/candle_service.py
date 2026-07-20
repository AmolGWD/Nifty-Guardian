from datetime import datetime, timedelta
import os

from dotenv import load_dotenv
from kiteconnect import KiteConnect

from app.auth.token_store import token_store

load_dotenv()


class CandleService:

    def __init__(self):

        self.api_key = os.getenv("KITE_API_KEY")

        self.instrument_token = 256265  # NIFTY 50 Index

        self.interval = "15minute"

        self.cache = None

        self.cache_time = None

    def get_candles(self):

        # Cache candles for 30 seconds
        if self.cache is not None and self.cache_time is not None:

            if (datetime.now() - self.cache_time).seconds < 30:

                return self.cache

        access_token = token_store.access_token()

        kite = KiteConnect(api_key=self.api_key)

        kite.set_access_token(access_token)

        to_date = datetime.now()

        from_date = to_date - timedelta(days=10)

        candles = kite.historical_data(

            instrument_token=self.instrument_token,

            from_date=from_date,

            to_date=to_date,

            interval=self.interval,

            continuous=False,

            oi=False

        )

        self.cache = candles

        self.cache_time = datetime.now()

        return candles


candle_service = CandleService()