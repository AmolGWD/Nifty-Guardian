from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
import os

from dotenv import load_dotenv
from kiteconnect import KiteConnect

from app.auth.token_store import token_store

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class OptionChainService:
    """
    Existing Option Chain service used by Signal Engine.
    """

    def __init__(self):
        self.api_key = os.getenv("KITE_API_KEY")
        self.instrument_cache = None

    def _kite(self):
        kite = KiteConnect(api_key=self.api_key)
        kite.set_access_token(token_store.access_token())
        return kite

    def instruments(self):
        if self.instrument_cache is None:
            self.instrument_cache = self._kite().instruments("NFO")
        return self.instrument_cache

    def nearest_expiry(self):
        expiries = sorted(
            {
                i["expiry"]
                for i in self.instruments()
                if i["name"] == "NIFTY"
            }
        )
        return expiries[0]

    def atm_strike(self, spot):
        return round(spot / 50) * 50

    def get_option_chain(self, spot):
        expiry = self.nearest_expiry()
        atm = self.atm_strike(spot)

        strikes = [
            atm - 200,
            atm - 150,
            atm - 100,
            atm - 50,
            atm,
            atm + 50,
            atm + 100,
            atm + 150,
            atm + 200,
        ]

        chain = []

        for ins in self.instruments():
            if (
                ins["name"] == "NIFTY"
                and ins["expiry"] == expiry
                and ins["strike"] in strikes
            ):
                chain.append(ins)

        return chain


option_chain_service = OptionChainService()


# ==========================================================
# Paper Trading Option Data Interface
# ==========================================================

class OptionDataService(ABC):

    @abstractmethod
    def get_spot_price(self) -> float:
        pass

    @abstractmethod
    def get_atm_strike(self) -> int:
        pass

    @abstractmethod
    def get_expiry(self) -> date:
        pass

    @abstractmethod
    def get_option_premium(
        self,
        strike: int,
        option_type: str,
        expiry: date,
    ) -> float:
        pass

    @abstractmethod
    def get_lot_size(self) -> int:
        pass


# Keep this import at the bottom to avoid circular imports.
from app.market.zerodha_option_data_service import ZerodhaOptionDataService

option_data_service = ZerodhaOptionDataService()