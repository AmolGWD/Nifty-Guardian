class RuleEngine:

    def evaluate(self, market, indicators):

        rules = {

            "EMA": {
                "passed": indicators["EMA"],
                "weight": 20,
                "reason": "Price above EMA"
            },

            "RSI": {
                "passed": indicators["RSI"],
                "weight": 15,
                "reason": "RSI above 55"
            },

            "Supertrend": {
                "passed": indicators["Supertrend"],
                "weight": 20,
                "reason": "Supertrend Green"
            },

            "PCR": {
                "passed": market["pcr"] > 1,
                "weight": 15,
                "reason": "PCR Bullish"
            },

            "OI": {
                "passed": market["oi_bias"] == "Bullish",
                "weight": 10,
                "reason": "Bullish OI"
            },

            "Market Mood": {
                "passed": market["market_mood"] == "Bullish",
                "weight": 10,
                "reason": "Market Bullish"
            },

            "Trend": {
                "passed": "Uptrend" in market["trend"],
                "weight": 10,
                "reason": "Trend Up"
            }

        }

        return rules


rule_engine = RuleEngine()