class SignalService:

    def generate_signal(self, market, indicators):

        score = indicators["guardian_score"]

        price = market["price"]

        signal = "WAIT"

        confidence = score

        status = "Waiting"

        entry = round(price)

        stop_loss = round(price - 40)

        target1 = round(price + 40)

        target2 = round(price + 90)

        # Strong Bullish

        if score >= 80:

            signal = "BUY CE"

            confidence = score

            status = "Active"

        # Strong Bearish

        elif (
            not indicators["EMA"]
            and not indicators["RSI"]
            and not indicators["Supertrend"]
        ):

            signal = "BUY PE"

            confidence = 85

            status = "Active"

            stop_loss = round(price + 40)

            target1 = round(price - 40)

            target2 = round(price - 90)

        # Neutral

        else:

            signal = "WAIT"

            confidence = score

            status = "Waiting"

        return {

            "signal": signal,

            "confidence": confidence,

            "status": status,

            "entry": entry,

            "stop_loss": stop_loss,

            "target1": target1,

            "target2": target2

        }


signal_service = SignalService()