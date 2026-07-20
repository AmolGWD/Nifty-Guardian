<<<<<<< ours
from kiteconnect import KiteConnect
from dotenv import load_dotenv
from pathlib import Path
import os

from app.auth.token_store import token_store

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class OptionChainService:

    def __init__(self):

        self.api_key = os.getenv("KITE_API_KEY")

        self.instrument_cache = None

    def _kite(self):

        kite = KiteConnect(api_key=self.api_key)

        kite.set_access_token(
            token_store.access_token()
        )

        return kite

    def instruments(self):

        if self.instrument_cache is None:

            self.instrument_cache = self._kite().instruments("NFO")

        return self.instrument_cache

    def nearest_expiry(self):

        expiries = sorted(
            list(
                {
                    i["expiry"]
                    for i in self.instruments()
                    if i["name"] == "NIFTY"
                }
            )
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

        instruments = self.instruments()

        for ins in instruments:

            if (

                ins["name"] == "NIFTY"

                and ins["expiry"] == expiry

                and ins["strike"] in strikes

            ):

                chain.append(ins)

        return chain


option_chain_service = OptionChainService()
=======
"""
========================================
 NIFTY Guardian Option Data Interface
========================================

Paper trading logic depends only on this interface, never on a
specific broker/exchange implementation. The active provider is
wired up at the bottom of this file - swapping providers means
changing that one line, nothing else in the codebase.
"""

from abc import ABC, abstractmethod
from datetime import date


class OptionDataService(ABC):
    """
    Abstract contract for option market data required by paper trading.
    """

    @abstractmethod
    def get_spot_price(self) -> float:
        """Current NIFTY spot price."""

    @abstractmethod
    def get_atm_strike(self) -> int:
        """Current at-the-money strike, derived from live spot."""

    @abstractmethod
    def get_expiry(self) -> date:
        """Nearest weekly expiry date."""

    @abstractmethod
    def get_option_premium(self, strike: int, option_type: str, expiry: date) -> float:
        """Current live premium for the given CE/PE contract."""

    @abstractmethod
    def get_lot_size(self) -> int:
        """Current lot size for one NIFTY option lot."""


# --------------------------------------------------------------------
# Composition root.
#
# This import is intentionally placed after OptionDataService is
# defined (not at the top of the file) so that ZerodhaOptionDataService
# can import OptionDataService from this module without a circular
# import error. Do not move it above the class definition.
# --------------------------------------------------------------------

from app.market.zerodha_option_data_service import ZerodhaOptionDataService  # noqa: E402

option_data_service = ZerodhaOptionDataService()
>>>>>>> theirs
