from datetime import datetime
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


class SignalManager:

    def __init__(self):

        self.active_trade = None

        self.daily_signals = []

        self.today = datetime.now(IST).date()

    def qualify(self, trade):

        now = datetime.now(IST)

        # Reset every day
        if now.date() != self.today:

            self.today = now.date()

            self.daily_signals = []

            self.active_trade = None

        # Max 5 trades
        if len(self.daily_signals) >= 5:

            trade["signal"] = "NO TRADE"

            trade["status"] = "Daily Limit"

            return trade

        # Only one active trade
        if self.active_trade:

            trade["signal"] = "WAIT"

            trade["status"] = "Trade Active"

            return trade

        # Confidence filter
        if trade["confidence"] < 90:

            trade["signal"] = "WAIT"

            trade["status"] = "Low Confidence"

            return trade

        # Risk Reward
        rr = float(trade["risk_reward"].split(":")[1])

        if rr < 1:

            trade["signal"] = "WAIT"

            trade["status"] = "Poor RR"

            return trade

        self.active_trade = trade

        self.daily_signals.append(trade)

        trade["status"] = "🟢 Active"

        return trade


signal_manager = SignalManager()