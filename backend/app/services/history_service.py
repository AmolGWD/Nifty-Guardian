from datetime import datetime
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


class HistoryService:

    def __init__(self):

        self.history = []

        self.last_signal = None

    def update_history(self, trade):

        # Store a new record only when the signal changes
        if trade["signal"] != self.last_signal:

            self.last_signal = trade["signal"]

            current_time = datetime.now(IST)

            record = {

                "id": f"NG-{len(self.history)+1:03}",

                "time": current_time.strftime("%H:%M"),

                "timestamp": current_time.strftime("%d-%b-%Y %I:%M:%S %p"),

                "signal": trade["signal"],

                "confidence": trade["confidence"],

                "status": trade["status"]

            }

            self.history.insert(0, record)

        return self.history

    def latest_signal_time(self):

        if not self.history:

            return "-"

        return self.history[0]["timestamp"]


history_service = HistoryService()