from app.config.settings import APP_NAME
from app.config.settings import VERSION
from app.config.settings import MIN_CONFIDENCE
from app.config.settings import TIMEFRAME

from app.services.market_session import get_market_status

print("=" * 50)
print(f"🛡️ {APP_NAME}")
print("=" * 50)

print(f"Version             : {VERSION}")
print(f"Time Frame          : {TIMEFRAME}")
print(f"Minimum Confidence  : {MIN_CONFIDENCE}%")
print(f"Market Status       : {get_market_status()}")

print("=" * 50)