from datetime import datetime

from app.signals.models import (
    DailyPerformanceReport,
    DummyTrade,
    DummyTradeStatus,
    ExitReason,
    GuardianScore,
)
from app.trading.strategy.models import StrategyDirection, StrategyStrength


def make_score(**overrides: object) -> GuardianScore:
    base: dict[str, object] = dict(
        score=90.0, strength=StrategyStrength.STRONG, reward_risk_ratio=2.0,
        reasons=["EMA alignment: price above EMA", "RSI confirmation: RSI 62.00 above 55"],
    )
    base.update(overrides)
    return GuardianScore(**base)


def make_open_trade(**overrides: object) -> DummyTrade:
    base: dict[str, object] = dict(
        trade_id="11111111-2222-3333-4444-555555555555",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        guardian_score=make_score(),
        entry_price=100.0,
        stop_loss=95.0,
        target=115.0,
        quantity=50,
        opened_at=datetime(2026, 1, 5, 9, 30),
        status=DummyTradeStatus.OPEN,
    )
    base.update(overrides)
    return DummyTrade(**base)


def make_closed_trade(**overrides: object) -> DummyTrade:
    trade = make_open_trade()
    base: dict[str, object] = dict(
        exit_price=115.0,
        closed_at=datetime(2026, 1, 5, 11, 0),
        pnl=750.0,
        exit_reason=ExitReason.TARGET,
    )
    base.update(overrides)
    return trade.close(**base)  # type: ignore[arg-type]


def make_report(**overrides: object) -> DailyPerformanceReport:
    base: dict[str, object] = dict(
        report_date="2026-01-05",
        total_signals=2,
        winning_trades=1,
        losing_trades=1,
        win_rate=50.0,
        net_points=100.0,
        average_reward_risk_ratio=2.0,
        best_trade=make_closed_trade(),
        worst_trade=make_closed_trade(pnl=-50.0, exit_reason=ExitReason.STOP_LOSS),
    )
    base.update(overrides)
    return DailyPerformanceReport(**base)
