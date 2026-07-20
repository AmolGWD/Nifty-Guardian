import pandas as pd

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from app.market.candle_service import candle_service


class IndicatorService:

    def calculate_indicators(self, market):

        candles = candle_service.get_candles()

        df = pd.DataFrame(candles)

        df.rename(
            columns={
                "date": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            },
            inplace=True
        )

        # EMA
        df["EMA16"] = EMAIndicator(
            close=df["Close"],
            window=16
        ).ema_indicator()

        # RSI
        df["RSI"] = RSIIndicator(
            close=df["Close"],
            window=14
        ).rsi()

        # ATR
        atr = AverageTrueRange(
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            window=10
        )

        df["ATR"] = atr.average_true_range()

        # VWAP
        tp = (df["High"] + df["Low"] + df["Close"]) / 3

        volume = df["Volume"].replace(0, 1)

        df["VWAP"] = (
            (tp * volume).cumsum()
            /
            volume.cumsum()
        )

        # -------- Supertrend --------

        multiplier = 3

        hl2 = (df["High"] + df["Low"]) / 2

        upperband = hl2 + multiplier * df["ATR"]

        lowerband = hl2 - multiplier * df["ATR"]

        supertrend = [True]

        for i in range(1, len(df)):

            if df["Close"].iloc[i] > upperband.iloc[i - 1]:
                supertrend.append(True)

            elif df["Close"].iloc[i] < lowerband.iloc[i - 1]:
                supertrend.append(False)

            else:
                supertrend.append(supertrend[-1])

        df["Supertrend"] = supertrend

        latest = df.iloc[-1]

        price = market["price"]

        ema = float(latest["EMA16"])

        rsi = float(latest["RSI"])

        vwap = float(latest["VWAP"])

        st = bool(latest["Supertrend"])

        score = 0

        if price > ema:
            score += 20

        if rsi > 55:
            score += 20

        if st:
            score += 20

        if price > vwap:
            score += 20

        score += 20

        return {

            "EMA": price > ema,

            "RSI": rsi > 55,

            "Supertrend": st,

            "Resistance": False,

            "OI": True,

            "VWAP": price > vwap,

            "ema_value": round(ema, 2),

            "rsi_value": round(rsi, 2),

            "vwap_value": round(vwap, 2),

            "atr": round(float(latest["ATR"]), 2),

            "guardian_score": score

        }


indicator_service = IndicatorService()