from app.config.settings import *
from app.models.market_data import MarketData
from app.services.market_session import get_market_status
from app.strategy.signal_engine import generate_signal


data = MarketData(
    current_price=24280,
    previous_close=24220,
    open_price=24255,
    ema=24240,
    rsi=58,
    supertrend_green=True,
    resistance=24270,
    support=24180,
    ce_oi=120000,
    pe_oi=180000,
)


print("=" * 50)
print(f"🛡️ {APP_NAME}")
print("=" * 50)

print(f"Version             : {VERSION}")
print(f"Time Frame          : {TIMEFRAME}")
print(f"Minimum Confidence  : {MIN_CONFIDENCE}%")
print(f"Market Status       : {get_market_status()}")

print("-" * 50)

print("Strategy Output")

signal = generate_signal(data)

print(f"Signal      : {signal.action}")
print(f"Confidence  : {signal.confidence}%")
print("Reasons")

for reason in signal.reasons:
    print(f"  • {reason}")

print("=" * 50)