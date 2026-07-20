"""
========================================
 NIFTY Guardian Configuration
========================================
"""

import os

# --------------------------------------
# Application
# --------------------------------------

APP_NAME = "NIFTY Guardian"
VERSION = "2.0"

# --------------------------------------
# Trading Settings
# --------------------------------------

TIMEFRAME = "15m"

# --------------------------------------
# Technical Indicators
# --------------------------------------

EMA_PERIOD = 20

RSI_BUY = 55
RSI_SELL = 45

SUPER_TREND_PERIOD = 10
SUPER_TREND_MULTIPLIER = 3

# --------------------------------------
# Confidence System
# --------------------------------------

EMA_SCORE = 20
SUPERTREND_SCORE = 20
RSI_SCORE = 20
BREAKOUT_SCORE = 20
OI_SCORE = 20

MIN_CONFIDENCE = 70

# --------------------------------------
# Risk Management
# --------------------------------------

ENTRY_BUFFER = 2

STOPLOSS_BUFFER = 20

RISK_REWARD = 2

# --------------------------------------
# Trading Window
# --------------------------------------

MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"

# --------------------------------------
# Option Selection
# --------------------------------------

STRIKE_STEP = 50

DEFAULT_LOT_SIZE = 75

# --------------------------------------
# Logging
# --------------------------------------

ENABLE_LOGGING = True

LOG_LEVEL = "INFO"

# --------------------------------------
# Zerodha Kite Connect
# (credentials are read from environment variables only)
# --------------------------------------

KITE_API_KEY = os.environ.get("KITE_API_KEY", "")
KITE_API_SECRET = os.environ.get("KITE_API_SECRET", "")
KITE_ACCESS_TOKEN = os.environ.get("KITE_ACCESS_TOKEN", "")

# --------------------------------------
# Telegram Alerts
# --------------------------------------

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# --------------------------------------
# Paper Trading Database
# --------------------------------------

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(_BACKEND_DIR, 'data', 'paper_trades.db')}",
)