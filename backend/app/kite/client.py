"""
Factory for the KiteConnect SDK client.

Kept separate from KiteAuthService so it can be swapped for a fake in
tests without touching auth logic, and so KiteAuthService itself never
imports kiteconnect directly.
"""

from kiteconnect import KiteConnect

from app.core.config import settings


def build_kite_client() -> KiteConnect:
    if not settings.kite_api_key:
        raise RuntimeError("KITE_API_KEY is not configured")

    return KiteConnect(api_key=settings.kite_api_key)
