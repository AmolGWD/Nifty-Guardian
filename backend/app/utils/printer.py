"""
========================================
 NIFTY Guardian Signal Printer
========================================
"""

from datetime import datetime

from app.config.settings import APP_NAME
from app.config.settings import VERSION
from app.services.market_session import get_market_status


def print_signal(signal, data):

    print()
    print("=" * 60)
    print(f"🛡️  {APP_NAME}")
    print("=" * 60)

    print(f"Version             : {VERSION}")
    print(f"Date & Time         : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    print(f"Market Status       : {get_market_status()}")

    print("-" * 60)

    print(f"NIFTY Price         : {data.current_price}")
    print(f"EMA                 : {data.ema}")
    print(f"RSI                 : {data.rsi}")

    print("-" * 60)

    print(f"Signal              : {signal.action}")
    print(f"Confidence          : {signal.confidence}%")

    if signal.entry > 0:
        print(f"Entry               : {signal.entry}")
        print(f"Stop Loss           : {signal.stop_loss}")
        print(f"Target 1            : {signal.target1}")
        print(f"Target 2            : {signal.target2}")

    print("-" * 60)

    print("Reasons")

    for reason in signal.reasons:
        print(f"✅ {reason}")

    print("=" * 60)
    print()