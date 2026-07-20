from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.market_service import market_service
from app.services.indicator_service import indicator_service
from app.services.signal_service import signal_service
from app.services.history_service import history_service
from app.services.performance_service import performance_service
from app.services.paper_trade_service import paper_trade_service
from app.services.paper_trade_orchestrator import paper_trade_orchestrator

from fastapi.responses import RedirectResponse

from app.auth.kite_auth import kite_auth
from app.auth.token_store import token_store


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
    return {
        "message": "NIFTY Guardian API Running"
    }


@app.get("/kite/login")
def kite_login():
    return RedirectResponse(
        kite_auth.login_url()
    )


@app.get("/login")
def login(request_token: str):

    session = kite_auth.generate_session(request_token)
    token_store.save(session)

    return {
        "status": "SUCCESS",
        "message": "Kite Connected Successfully",
        "user": session["user_name"]
    }


@app.get("/signal")
def get_signal():

    # 1. Get Market Data
    try:
    market = market_service.get_market_data()
except TokenException:
    raise HTTPException(
        status_code=401,
        detail="Kite session expired. Please login again."
    )

    # 2. Calculate Indicators
    indicators = indicator_service.calculate_indicators(market)

    # 3. Generate Trading Signal
    trade = signal_service.generate_signal(
        market,
        indicators
    )

    # Paper Trading
    paper_trade_orchestrator.process(trade, indicators)

    # 4. Update History
    history = history_service.update_history(trade)

    # 5. Calculate Performance
    performance = performance_service.calculate(history)

    # 6. Get Latest Signal Time
    signal_time = history_service.latest_signal_time()

    # 7. Return Response
    return {

        # Market Data
        "symbol": market["symbol"],
        "price": market["price"],
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
        "last_refresh": market["last_refresh"],

        # Trading Signal
        "signal": trade["signal"],
        "confidence": trade["confidence"],
        "market_state": trade["market_state"],
        "status": trade["status"],

        # Trade Levels
        "entry": trade["entry"],
        "stop_loss": trade["stop_loss"],
        "target1": trade["target1"],
        "target2": trade["target2"],
        "risk_reward": trade["risk_reward"],

        # Signal Time
        "timestamp": signal_time,

        # Indicators
        "indicators": indicators,

        # Guardian Analysis
        "guardian": {
            "confidence": trade["confidence"],
            "stars": trade["stars"],
            "passed_rules": trade["passed_rules"],
            "failed_rules": trade["failed_rules"]
        },

        # History
        "history": history,

        # Performance
        "performance": performance
    }


@app.get("/paper-trades/open")
def paper_trades_open():
    return paper_trade_service.get_open_trades()


@app.get("/paper-trades/closed")
def paper_trades_closed():
    return paper_trade_service.get_closed_trades()


@app.get("/paper-trades/summary")
def paper_trades_summary():
    return paper_trade_service.get_summary()