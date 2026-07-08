class IndicatorService:

    def calculate_indicators(self, market):

        price = market["price"]

        ema = price - 18

        rsi = 61.8

        supertrend = True

        resistance = False

        oi = True

        score = 0

        if price > ema:
            score += 20

        if rsi > 55:
            score += 20

        if supertrend:
            score += 20

        if oi:
            score += 20

        if not resistance:
            score += 20

        return {

            "EMA": price > ema,

            "RSI": rsi > 55,

            "Supertrend": supertrend,

            "Resistance": resistance,

            "OI": oi,

            "ema_value": round(ema, 2),

            "rsi_value": rsi,

            "guardian_score": score

        }


indicator_service = IndicatorService()