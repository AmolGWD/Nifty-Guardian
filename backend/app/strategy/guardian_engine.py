from app.strategy.engine.rule_engine import rule_engine
from app.strategy.engine.score_engine import score_engine
from app.strategy.engine.decision_engine import decision_engine
from app.strategy.engine.risk_engine import risk_engine


class GuardianEngine:

    def evaluate(self, market, indicators):

        # Step 1: Evaluate Rules
        rules = rule_engine.evaluate(
            market,
            indicators
        )

        # Step 2: Calculate Confidence Score
        score = score_engine.calculate(
            rules
        )

        # Step 3: Make Trading Decision
        decision = decision_engine.decide(
            score["confidence"]
        )

        # Pass confidence to Risk Engine
        decision["confidence"] = score["confidence"]

        # Step 4: Build Trade Plan
        risk = risk_engine.calculate(
            market,
            decision
        )

        return {

            "confidence": score["confidence"],

            "stars": score["stars"],

            "passed_rules": score["passed"],

            "failed_rules": score["failed"],

            "market_state": decision["market_state"],

            "signal": decision["signal"],

            "status": decision["status"],

            "entry": risk["entry"],

            "stop_loss": risk["stop_loss"],

            "target1": risk["target1"],

            "target2": risk["target2"],

            "risk_reward": risk["risk_reward"]

        }


guardian_engine = GuardianEngine()