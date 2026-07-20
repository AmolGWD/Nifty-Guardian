"""
========================================
 NIFTY Guardian Paper Trade Orchestrator
========================================

Decides WHEN paper trades are opened, monitored, and closed, using
the Signal Engine's own entry/stop_loss/target1 values. PaperTradeService
only ever records what this orchestrator decides - it never makes a
trading decision itself.
"""

from datetime import datetime

from app.alerts import telegram
from app.config.settings import MARKET_CLOSE
from app.market.option_chain import option_data_service
from app.services.paper_trade_service import paper_trade_service

MILESTONE_THRESHOLDS = (25, 50, 75, 100)
DIRECTIONAL_SIGNALS = ("BUY CE", "BUY PE")


class PaperTradeOrchestrator:

    def __init__(self):
        self._last_signal = None
        self._last_daily_summary_date = None

    def process(self, trade: dict, indicators: dict) -> None:
        try:
            self._monitor_open_trades()
            self._handle_signal(trade, indicators)
            self._maybe_send_daily_summary()
        except Exception as exc:  # noqa: BLE001 - must never break /signal
            telegram.notify_system_error(str(exc))

    # ------------------------------------------------------------
    # Monitoring open trades against Signal Engine levels
    # ------------------------------------------------------------

    def _monitor_open_trades(self):
        open_trades = paper_trade_service.get_open_trades()
        if not open_trades:
            return

        current_spot = option_data_service.get_spot_price()
        now_time = datetime.now().strftime("%H:%M")

        for open_trade in open_trades:
            self._evaluate_trade(open_trade, current_spot, now_time)

    def _evaluate_trade(self, open_trade, current_spot, now_time):
        exit_reason = self._exit_reason(open_trade, current_spot, now_time)
        expiry = self._parse_expiry(open_trade["expiry"])

        if exit_reason:
            self._close(open_trade, expiry, current_spot, exit_reason)
        else:
            current_premium = option_data_service.get_option_premium(
                open_trade["strike"], open_trade["option_type"], expiry
            )
            paper_trade_service.update_trade(open_trade["id"], {
                "current_spot": current_spot,
                "current_premium": current_premium,
            })

    @staticmethod
    def _exit_reason(open_trade, current_spot, now_time):
        target = open_trade.get("target1")
        stop_loss = open_trade.get("stop_loss")

        if open_trade["option_type"] == "CE":
            if target is not None and current_spot >= target:
                return "TARGET"
            if stop_loss is not None and current_spot <= stop_loss:
                return "STOPLOSS"
        else:
            if target is not None and current_spot <= target:
                return "TARGET"
            if stop_loss is not None and current_spot >= stop_loss:
                return "STOPLOSS"

        if now_time >= MARKET_CLOSE:
            return "TIME_EXIT"

        return None

    def _close(self, open_trade, expiry, current_spot, exit_reason):
        exit_premium = option_data_service.get_option_premium(
            open_trade["strike"], open_trade["option_type"], expiry
        )
        closed = paper_trade_service.close_trade(open_trade["id"], {
            "exit_spot": current_spot,
            "exit_premium": exit_premium,
            "exit_reason": exit_reason,
        })
        telegram.notify_trade_closed(closed)
        self._maybe_send_milestone()
        return closed

    # ------------------------------------------------------------
    # Opening new trades on signal change
    # ------------------------------------------------------------

    def _handle_signal(self, trade: dict, indicators: dict):
        signal = trade.get("signal")

        if signal == self._last_signal:
            return

        self._last_signal = signal
        telegram.notify_signal_generated(trade)

        if signal not in DIRECTIONAL_SIGNALS:
            return

        self._close_for_reversal()
        self._open_trade(trade, indicators, signal)

    def _close_for_reversal(self):
        for open_trade in paper_trade_service.get_open_trades():
            expiry = self._parse_expiry(open_trade["expiry"])
            current_spot = option_data_service.get_spot_price()
            self._close(open_trade, expiry, current_spot, "REVERSED")

    def _open_trade(self, trade: dict, indicators: dict, signal: str):
        option_type = "CE" if signal == "BUY CE" else "PE"
        expiry = option_data_service.get_expiry()
        spot = option_data_service.get_spot_price()
        strike = option_data_service.get_atm_strike()
        premium = option_data_service.get_option_premium(strike, option_type, expiry)
        lot_size = option_data_service.get_lot_size()

        created = paper_trade_service.create_trade({
            "option_type": option_type,
            "strike": strike,
            "expiry": expiry.isoformat(),
            "entry_spot": spot,
            "entry_premium": premium,
            "quantity": lot_size,
            "stop_loss": trade.get("stop_loss"),
            "target1": trade.get("target1"),
            "target2": trade.get("target2"),
            "confidence": trade.get("confidence"),
            "guardian_score": indicators.get("guardian_score"),
            "indicator_snapshot": indicators,
        })

        telegram.notify_trade_opened(created)

    # ------------------------------------------------------------
    # Periodic notifications
    # ------------------------------------------------------------

    def _maybe_send_milestone(self):
        summary = paper_trade_service.get_summary()
        if summary.get("closed_count") in MILESTONE_THRESHOLDS:
            telegram.notify_milestone(summary["closed_count"], summary)

    def _maybe_send_daily_summary(self):
        now = datetime.now()
        if now.strftime("%H:%M") < MARKET_CLOSE:
            return

        today = now.strftime("%Y-%m-%d")
        if self._last_daily_summary_date == today:
            return

        self._last_daily_summary_date = today
        telegram.notify_daily_summary(paper_trade_service.get_summary())

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    @staticmethod
    def _parse_expiry(expiry_str: str):
        return datetime.strptime(expiry_str, "%Y-%m-%d").date()


paper_trade_orchestrator = PaperTradeOrchestrator()
