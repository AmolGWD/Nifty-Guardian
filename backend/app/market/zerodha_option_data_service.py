"""
========================================
 NIFTY Guardian Zerodha Option Data Service
========================================

All broker-specific (Zerodha Kite Connect) code lives in this file
only. Nothing outside this file imports kiteconnect.
"""

import csv
import os
from datetime import date, datetime

from kiteconnect import KiteConnect

from app.config.settings import (
    DEFAULT_LOT_SIZE,
    KITE_ACCESS_TOKEN,
    KITE_API_KEY,
    STRIKE_STEP,
)
from app.market.option_chain import OptionDataService

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INSTRUMENT_CACHE_PATH = os.path.join(_BACKEND_DIR, "data", "instruments_nfo.csv")

NIFTY_SPOT_SYMBOL = "NSE:NIFTY 50"

INSTRUMENT_FIELDS = [
    "instrument_token",
    "tradingsymbol",
    "name",
    "expiry",
    "strike",
    "lot_size",
    "instrument_type",
]


class ZerodhaOptionDataService(OptionDataService):
    """
    Live NIFTY option data sourced from Zerodha Kite Connect.
    """

    def __init__(self):
        self._kite = KiteConnect(api_key=KITE_API_KEY)
        if KITE_ACCESS_TOKEN:
            self._kite.set_access_token(KITE_ACCESS_TOKEN)
        self._instrument_cache = None

    # ------------------------------------------------------------
    # OptionDataService interface
    # ------------------------------------------------------------

    def get_spot_price(self) -> float:
        quote = self._kite.ltp(NIFTY_SPOT_SYMBOL)
        return float(quote[NIFTY_SPOT_SYMBOL]["last_price"])

    def get_atm_strike(self) -> int:
        spot = self.get_spot_price()
        return int(round(spot / STRIKE_STEP) * STRIKE_STEP)

    def get_expiry(self) -> date:
        today = date.today()
        expiries = sorted({
            row["expiry"] for row in self._nifty_option_rows()
            if row["expiry"] >= today
        })

        if not expiries:
            raise RuntimeError(
                "No upcoming NIFTY option expiry found in the NFO instrument dump"
            )

        return expiries[0]

    def get_option_premium(self, strike: int, option_type: str, expiry: date) -> float:
        row = self._find_option_row(strike, option_type, expiry)
        symbol = f"NFO:{row['tradingsymbol']}"
        quote = self._kite.ltp(symbol)
        return float(quote[symbol]["last_price"])

    def get_lot_size(self) -> int:
        rows = self._nifty_option_rows()
        if rows:
            return int(float(rows[0]["lot_size"]))
        return DEFAULT_LOT_SIZE

    # ------------------------------------------------------------
    # Instrument dump caching (refreshed once per day)
    # ------------------------------------------------------------

    def _nifty_option_rows(self):
        return [
            row for row in self._load_instrument_dump()
            if row["name"] == "NIFTY" and row["instrument_type"] in ("CE", "PE")
        ]

    def _find_option_row(self, strike: int, option_type: str, expiry: date):
        for row in self._nifty_option_rows():
            if (
                row["expiry"] == expiry
                and row["instrument_type"] == option_type
                and int(float(row["strike"])) == int(strike)
            ):
                return row

        raise RuntimeError(
            f"No NFO instrument found for NIFTY {strike} {option_type} {expiry}"
        )

    def _load_instrument_dump(self):
        if self._instrument_cache is not None:
            return self._instrument_cache

        if not self._cache_is_fresh():
            self._refresh_cache()

        self._instrument_cache = self._read_cache()
        return self._instrument_cache

    def _cache_is_fresh(self) -> bool:
        if not os.path.exists(INSTRUMENT_CACHE_PATH):
            return False

        modified = datetime.fromtimestamp(os.path.getmtime(INSTRUMENT_CACHE_PATH))
        return modified.date() == date.today()

    def _refresh_cache(self):
        instruments = self._kite.instruments("NFO")

        os.makedirs(os.path.dirname(INSTRUMENT_CACHE_PATH), exist_ok=True)

        with open(INSTRUMENT_CACHE_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=INSTRUMENT_FIELDS)
            writer.writeheader()
            for row in instruments:
                writer.writerow({key: row.get(key) for key in INSTRUMENT_FIELDS})

    def _read_cache(self):
        rows = []

        with open(INSTRUMENT_CACHE_PATH, newline="") as f:
            for row in csv.DictReader(f):
                rows.append({
                    "instrument_token": row["instrument_token"],
                    "tradingsymbol": row["tradingsymbol"],
                    "name": row["name"],
                    "expiry": datetime.strptime(row["expiry"], "%Y-%m-%d").date(),
                    "strike": row["strike"],
                    "lot_size": row["lot_size"],
                    "instrument_type": row["instrument_type"],
                })

        return rows
