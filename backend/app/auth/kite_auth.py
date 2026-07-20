import os
from pathlib import Path

from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Load backend/.env
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class KiteAuth:

    def __init__(self):

        self.api_key = os.getenv("KITE_API_KEY")
        self.api_secret = os.getenv("KITE_API_SECRET")

        print("=" * 50)
        print("KITE_API_KEY :", self.api_key)
        print("SECRET FOUND :", self.api_secret is not None)
        print("=" * 50)

        self.kite = KiteConnect(api_key=self.api_key)

    def login_url(self):

        return self.kite.login_url()

    def generate_session(self, request_token):

        return self.kite.generate_session(
            request_token,
            api_secret=self.api_secret
        )


kite_auth = KiteAuth()