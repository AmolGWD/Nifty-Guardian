from kiteconnect import KiteConnect
import json

with open("kite_token.json") as f:
    session = json.load(f)

kite = KiteConnect(api_key=session["api_key"])
kite.set_access_token(session["access_token"])

print(kite.profile())
print(kite.quote(["NSE:NIFTY 50"]))