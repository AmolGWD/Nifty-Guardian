class DecisionEngine:

    def decide(self, confidence):

        if confidence >= 80:

            return {
                "market_state": "Strong Bullish",
                "signal": "BUY CE",
                "status": "🟢 Active"
            }

        elif confidence >= 60:

            return {
                "market_state": "Sideways",
                "signal": "WAIT",
                "status": "⏳ Waiting"
            }

        elif confidence >= 40:

            return {
                "market_state": "Strong Bearish",
                "signal": "BUY PE",
                "status": "🔴 Active"
            }

        else:

            return {
                "market_state": "High Risk",
                "signal": "NO TRADE",
                "status": "⚠️ Stay Out"
            }


decision_engine = DecisionEngine()