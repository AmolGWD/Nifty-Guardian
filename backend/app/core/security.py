"""
Symmetric encryption for secrets stored at rest (e.g. Kite access
tokens), using Fernet (AES-128-CBC + HMAC) keyed by settings.secret_key.
"""

from functools import lru_cache

from cryptography.fernet import Fernet

from app.core.config import settings


@lru_cache
def _fernet() -> Fernet:
    return Fernet(settings.secret_key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()
