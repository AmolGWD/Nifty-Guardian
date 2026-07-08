from datetime import datetime


class HistoryService:

    def __init__(self):

        self.history = []

        self.last_signal = None

    def update_history(self, trade):

        # Only add a new record if signal changed
        if trade["signal"] != self.last_signal:

            self.last_signal = trade["signal"]

            record = {

                "id": f"NG-{len(self.history)+1:03}",

                "time": datetime.now().strftime("%H:%M"),

                "timestamp": datetime.now().strftime("%d-%b-%Y %I:%M:%S %p"),

                "signal": trade["signal"],

                "confidence": trade["confidence"],

                "status": trade["status"]

            }

            self.history.insert(0, record)

        return self.history

    def latest_signal_time(self):

        if len(self.history) == 0:

            return "-"

        return self.history[0]["timestamp"]


history_service = HistoryService()