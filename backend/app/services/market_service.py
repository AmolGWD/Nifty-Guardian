from datetime import datetime


class MarketService:

    def __init__(self):

        self.symbol = "NIFTY 50"

    def get_market_data(self):

        return {

            "symbol": self.symbol,

            "price": 24820.50,

            "change": 128.35,

            "open": 24720.50,

            "high": 24890.30,

            "low": 24690.25,

            "previous_close": 24692.15,

            "market_mood": "Bullish",

            "trend": "Strong Uptrend",

            "volatility": "Medium",

            "pcr": 1.18,

            "oi_bias": "Bullish",

            "last_refresh": datetime.now().strftime("%H:%M:%S")

        }


market_service = MarketService()