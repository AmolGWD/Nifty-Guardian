class RiskEngine:

    def calculate(self, market, decision):

        price = market["price"]

        signal = decision["signal"]

        confidence = decision["confidence"]

        # Dynamic Risk based on Confidence
        if confidence >= 90:

            sl_points = 30
            target1_points = 60
            target2_points = 120

        elif confidence >= 80:

            sl_points = 35
            target1_points = 70
            target2_points = 140

        elif confidence >= 60:

            sl_points = 45
            target1_points = 70
            target2_points = 100

        else:

            sl_points = 60
            target1_points = 60
            target2_points = 60

        if signal == "BUY CE":

            entry = round(price)

            stop_loss = round(price - sl_points)

            target1 = round(price + target1_points)

            target2 = round(price + target2_points)

        elif signal == "BUY PE":

            entry = round(price)

            stop_loss = round(price + sl_points)

            target1 = round(price - target1_points)

            target2 = round(price - target2_points)

        else:

            entry = round(price)

            stop_loss = round(price)

            target1 = round(price)

            target2 = round(price)

        return {

            "entry": entry,

            "stop_loss": stop_loss,

            "target1": target1,

            "target2": target2,

            "risk_reward": f"1:{round(target1_points/sl_points,2)}"

        }


risk_engine = RiskEngine()