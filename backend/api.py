from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NIFTY Guardian API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "NIFTY Guardian API Running"}


@app.get("/signal")
def signal():

    history = [
        {
            "id": "NG-001",
            "time": "09:18",
            "signal": "BUY CE",
            "confidence": 82,
            "status": "🟢 Active"
        },
        {
            "id": "NG-002",
            "time": "09:42",
            "signal": "BUY PE",
            "confidence": 91,
            "status": "🎯 Target 1"
        },
        {
            "id": "NG-003",
            "time": "10:15",
            "signal": "BUY CE",
            "confidence": 88,
            "status": "❌ Stop Loss"
        },
        {
            "id": "NG-004",
            "time": "10:46",
            "signal": "WAIT",
            "confidence": 61,
            "status": "⏳ Waiting"
        }
    ]

    return {

        "symbol": "NIFTY 50",

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

        "signal": "BUY CE",

        "confidence": 82,

        "status": "Active",

        "timestamp": "08-Jul-2026 09:18 AM",

        "entry": 24830,

        "stop_loss": 24790,

        "target1": 24870,

        "target2": 24920,

        "indicators": {

            "EMA": True,

            "RSI": True,

            "Supertrend": True,

            "Resistance": False,

            "OI": True

        },

        "history": history

    }