from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.market_service import market_service
from app.services.indicator_service import indicator_service
from app.services.signal_service import signal_service
from app.services.history_service import history_service
from app.services.performance_service import performance_service

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
market = market_service.get_market_data()
indicators = indicator_service.calculate_indicators(market)
trade = signal_service.generate_signal(
    market,
    indicators
)
history = history_service.update_history(trade)

performance = performance_service.calculate(history)

signal_time = history_service.latest_signal_time()
    return {

        "symbol": market["symbol"],

        ""price": market["price"],

        "change": market["change"],

        "open": market["open"],

        "high": market["high"],

        "low": market["low"],

        "previous_close": market["previous_close"],

        "market_mood": market["market_mood"],

        "trend": market["trend"],

        "volatility": market["volatility"],

        "pcr": market["pcr"],

        "oi_bias": market["oi_bias"],

        "signal": trade["signal"],

        "confidence": trade["confidence"],

        "status": trade["status"],

        "timestamp": signal_time,

        "entry": trade["entry"],

        "stop_loss": trade["stop_loss"],

        "target1": trade["target1"],

        "target2": trade["target2"],

        "indicators": indicators,

        "last_refresh": market["last_refresh"],

        "history": history,

        "performance": performance
    }