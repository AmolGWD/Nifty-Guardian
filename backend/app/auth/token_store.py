import json
import os


TOKEN_FILE = "kite_token.json"


class TokenStore:

    def save(self, session):

        # Convert datetime objects to strings
        serializable = {}

        for key, value in session.items():

            if hasattr(value, "isoformat"):
                serializable[key] = value.isoformat()
            else:
                serializable[key] = value

        with open(TOKEN_FILE, "w") as f:

            json.dump(serializable, f, indent=4)

    def load(self):

        if not os.path.exists(TOKEN_FILE):
            return None

        with open(TOKEN_FILE) as f:
            return json.load(f)

    def access_token(self):

        session = self.load()

        if session is None:
            return None

        return session.get("access_token")


token_store = TokenStore()