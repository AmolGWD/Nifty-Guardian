class EMARule:

    WEIGHT = 10

    def evaluate(self, market, indicators):

        passed = indicators.get("EMA", False)

        return {

            "name": "EMA",

            "passed": passed,

            "weight": self.WEIGHT,

            "reason": (
                "Price above EMA 16"
                if passed
                else "Price below EMA 16"
            )

        }


ema_rule = EMARule()