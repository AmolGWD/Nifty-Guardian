from app.market.candle_service import candle_service

candles = candle_service.get_candles()

print(len(candles))

print(candles[-1])