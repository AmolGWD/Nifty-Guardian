"""
Read-only market data endpoints.

This is the only place app.market_data is wired up to an actually
authenticated Kite session - the services themselves never import
app.kite or kiteconnect.
"""

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from kiteconnect import KiteConnect
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.kite.repository import KiteSessionRepository
from app.market_data.candles import candle_service
from app.market_data.client import KiteMarketDataClient, MarketDataClient
from app.market_data.expiry import expiry_discovery_service
from app.market_data.market_session import market_session_service
from app.market_data.option_chain import option_chain_service
from app.market_data.schemas import Candle, OptionContract, SpotPrice
from app.market_data.spot_price import spot_price_service

router = APIRouter(prefix="/market-data", tags=["Market Data"])


def get_market_data_client(db: Annotated[Session, Depends(get_db)]) -> MarketDataClient:
    access_token = KiteSessionRepository(db).get_valid_access_token()

    if access_token is None:
        raise HTTPException(
            status_code=401,
            detail="No valid Kite session. Log in via /auth/kite/login first.",
        )

    kite = KiteConnect(api_key=settings.kite_api_key)
    kite.set_access_token(access_token)

    return KiteMarketDataClient(kite)


MarketDataClientDep = Annotated[MarketDataClient, Depends(get_market_data_client)]


@router.get("/session")
def market_session() -> dict[str, str]:
    return {"status": market_session_service.get_status().value}


@router.get("/spot")
def spot_price(client: MarketDataClientDep) -> SpotPrice:
    return spot_price_service.get_spot_price(client)


@router.get("/candles")
def candles(
    client: MarketDataClientDep,
    instrument_token: int,
    from_date: datetime,
    to_date: datetime,
    interval: str = "15minute",
) -> list[Candle]:
    return candle_service.get_candles(client, instrument_token, from_date, to_date, interval)


@router.get("/expiries")
def expiries(client: MarketDataClientDep, underlying: str = "NIFTY") -> list[date]:
    return expiry_discovery_service.get_available_expiries(client, underlying)


@router.get("/option-chain")
def option_chain(
    client: MarketDataClientDep, expiry: date, underlying: str = "NIFTY"
) -> list[OptionContract]:
    return option_chain_service.get_option_chain(client, underlying, expiry)
