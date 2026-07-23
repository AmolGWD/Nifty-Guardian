"""
Owns every `DummyTrade` this engine has ever created - in-memory, the
same established pattern `app.paper_trading.execution_journal.
ExecutionJournal`/`app.research.experiment_registry.ExperimentRegistry`
already use. Never places a real order; every trade tracked here was
already a `PaperBroker` fill (frozen, `app.paper_trading`) - this class
only adds the richer per-trade reporting (R-multiple, duration, exit
reason) that `Position` itself doesn't carry.
"""

import uuid
from datetime import datetime

from app.signals.models import (
    DailyPerformanceReport,
    DummyTrade,
    DummyTradeStatus,
    ExitReason,
    GuardianScore,
)
from app.trading.strategy.models import StrategyDirection


class DummyTradeTracker:
    def __init__(self) -> None:
        self._trades: dict[str, DummyTrade] = {}

    def open_trade(
        self,
        *,
        strategy_name: str,
        direction: StrategyDirection,
        guardian_score: GuardianScore,
        entry_price: float,
        stop_loss: float,
        target: float,
        quantity: int,
        opened_at: datetime,
    ) -> DummyTrade:
        trade = DummyTrade(
            trade_id=str(uuid.uuid4()),
            strategy_name=strategy_name,
            direction=direction,
            guardian_score=guardian_score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            quantity=quantity,
            opened_at=opened_at,
        )
        self._trades[trade.trade_id] = trade
        return trade

    def close_trade(
        self, trade_id: str, *, exit_price: float, closed_at: datetime, pnl: float
    ) -> DummyTrade:
        trade = self._trades[trade_id]
        exit_reason = self._infer_exit_reason(trade, exit_price=exit_price)
        closed = trade.close(
            exit_price=exit_price, closed_at=closed_at, pnl=pnl, exit_reason=exit_reason
        )
        self._trades[trade_id] = closed
        return closed

    @staticmethod
    def _infer_exit_reason(trade: DummyTrade, *, exit_price: float) -> ExitReason:
        """
        `Position` (frozen) never carries an exit reason - only the
        realized P&L. Inferred here by comparing the actual exit price
        to this trade's own stored target/stop-loss, with a small
        tolerance for floating-point/candle-tick noise; anything that
        matches neither closely is reported as an honest EndOfDay/Unknown
        exit rather than a guessed-at reason.
        """
        tolerance = max(abs(trade.target - trade.entry_price) * 0.02, 0.01)
        if abs(exit_price - trade.target) <= tolerance:
            return ExitReason.TARGET
        if abs(exit_price - trade.stop_loss) <= tolerance:
            return ExitReason.STOP_LOSS
        return ExitReason.END_OF_DAY

    def get(self, trade_id: str) -> DummyTrade:
        return self._trades[trade_id]

    def open_trades(self) -> list[DummyTrade]:
        return [t for t in self._trades.values() if t.status == DummyTradeStatus.OPEN]

    def closed_trades(self) -> list[DummyTrade]:
        return sorted(
            (t for t in self._trades.values() if t.status == DummyTradeStatus.CLOSED),
            key=lambda t: t.closed_at or t.opened_at,
        )

    def all_trades(self) -> list[DummyTrade]:
        return list(self._trades.values())

    def trades_closed_on(self, day: datetime) -> list[DummyTrade]:
        return [
            t
            for t in self.closed_trades()
            if t.closed_at is not None and t.closed_at.date() == day.date()
        ]

    def trades_closed_between(self, start: datetime, end: datetime) -> list[DummyTrade]:
        return [
            t
            for t in self.closed_trades()
            if t.closed_at is not None and start.date() <= t.closed_at.date() <= end.date()
        ]

    @staticmethod
    def net_pnl(trades: list[DummyTrade]) -> float:
        return round(sum(t.pnl or 0.0 for t in trades), 2)

    @staticmethod
    def win_rate(trades: list[DummyTrade]) -> float:
        if not trades:
            return 0.0
        winners = sum(1 for t in trades if (t.pnl or 0.0) > 0)
        return round(winners / len(trades) * 100, 2)

    def build_daily_report(
        self,
        day: datetime,
        *,
        market_bias: StrategyDirection = StrategyDirection.NONE,
        guardian_status: str = "Active",
    ) -> DailyPerformanceReport:
        """
        `market_bias`/`guardian_status` are supplied by the caller
        (`SignalService`, which already tracks both) rather than
        recomputed here - this method stays purely a function of the
        closed-trade history it already owns, plus that small amount of
        caller-provided session context the trade history itself has no
        way of knowing.
        """
        trades = self.trades_closed_on(day)
        winners = [t for t in trades if (t.pnl or 0.0) > 0]
        losers = [t for t in trades if (t.pnl or 0.0) <= 0]
        net_points = sum(t.pnl or 0.0 for t in trades)
        average_rr = (
            sum(t.guardian_score.reward_risk_ratio for t in trades) / len(trades) if trades else 0.0
        )
        best_trade = max(trades, key=lambda t: t.pnl or 0.0) if trades else None
        worst_trade = min(trades, key=lambda t: t.pnl or 0.0) if trades else None
        durations = [t.duration_seconds for t in trades if t.duration_seconds is not None]

        return DailyPerformanceReport(
            report_date=day.date().isoformat(),
            total_signals=len(trades),
            buy_ce_count=sum(1 for t in trades if t.direction == StrategyDirection.LONG),
            buy_pe_count=sum(1 for t in trades if t.direction == StrategyDirection.SHORT),
            winning_trades=len(winners),
            losing_trades=len(losers),
            win_rate=round(len(winners) / len(trades) * 100, 2) if trades else 0.0,
            net_points=round(net_points, 2),
            average_pnl=round(net_points / len(trades), 2) if trades else 0.0,
            average_reward_risk_ratio=round(average_rr, 4),
            best_trade=best_trade,
            worst_trade=worst_trade,
            highest_guardian_score=(
                max(t.guardian_score.score for t in trades) if trades else 0.0
            ),
            average_hold_time_seconds=(
                round(sum(durations) / len(durations), 2) if durations else 0.0
            ),
            market_bias=market_bias,
            guardian_status=guardian_status,
        )
