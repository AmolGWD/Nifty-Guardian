class ScoreEngine:

    def calculate(self, rules):

        total_weight = 0
        score = 0
        passed_rules = []
        failed_rules = []

        for name, rule in rules.items():

            total_weight += rule["weight"]

            if rule["passed"]:

                score += rule["weight"]

                passed_rules.append(rule["reason"])

            else:

                failed_rules.append(rule["reason"])

        confidence = round((score / total_weight) * 100, 2)

        if confidence >= 80:

            stars = "★★★★★"

        elif confidence >= 60:

            stars = "★★★★☆"

        elif confidence >= 40:

            stars = "★★★☆☆"

        elif confidence >= 20:

            stars = "★★☆☆☆"

        else:

            stars = "★☆☆☆☆"

        return {

            "confidence": confidence,

            "stars": stars,

            "passed": passed_rules,

            "failed": failed_rules,

            "score": score,

            "maximum": total_weight

        }


score_engine = ScoreEngine()