class SupertrendRule:

    WEIGHT = 10

    def evaluate(self, market, indicators):

        passed = indicators.get("Supertrend", False)

        return {

            "name": "Supertrend",

            "passed": passed,

            "weight": self.WEIGHT,

            "reason": (
                "Price above Supertrend"
                if passed
                else "Price below Supertrend"
            )

        }


supertrend_rule = SupertrendRule()