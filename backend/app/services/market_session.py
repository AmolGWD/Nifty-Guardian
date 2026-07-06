from datetime import datetime

MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"


def get_market_status():
    now = datetime.now().strftime("%H:%M")

    if now < MARKET_OPEN:
        return "Pre Market"

    elif MARKET_OPEN <= now <= MARKET_CLOSE:
        return "Market Open"

    else:
        return "Market Closed"