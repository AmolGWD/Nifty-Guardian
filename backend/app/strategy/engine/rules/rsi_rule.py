class RSIRule:

    WEIGHT = 10

    def evaluate(self, market, indicators):

        rsi = indicators.get("RSI_Value", 50)

        passed = rsi > 55

        return {

            "name": "RSI",

            "passed": passed,

            "weight": self.WEIGHT,

            "reason": (
                f"RSI {rsi} Bullish"
                if passed
                else f"RSI {rsi} Weak"
            )

        }


rsi_rule = RSIRule()