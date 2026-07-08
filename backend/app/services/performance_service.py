class PerformanceService:

    def calculate(self, history):

        total = len(history)

        wins = 0
        losses = 0
        active = 0
        waiting = 0

        for trade in history:

            status = trade["status"]

            if "Target" in status:
                wins += 1

            elif "Stop" in status:
                losses += 1

            elif "Active" in status:
                active += 1

            else:
                waiting += 1

        accuracy = 0

        if (wins + losses) > 0:
            accuracy = round(
                (wins / (wins + losses)) * 100,
                2
            )

        return {

            "signals": total,

            "wins": wins,

            "losses": losses,

            "active": active,

            "waiting": waiting,

            "accuracy": accuracy,

            "risk_reward": "1 : 2",

            "pnl": "+0"

        }


performance_service = PerformanceService()