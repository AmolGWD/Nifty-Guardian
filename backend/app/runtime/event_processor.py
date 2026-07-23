"""
Per-candle orchestration - the CTO brief's exact ten-step flow:

    Receive Market Data -> Build IndicatorSnapshot -> Build MarketContext
    -> Evaluate TradingConditions -> Run Strategy Engine -> Run Risk
    Engine -> Publish Events -> Paper Broker -> Portfolio Update ->
    Journal -> Performance Monitor

No indicator, strategy, risk, or decision calculation happens in this
module - every one of those is a call into the package that already
owns it (Phases 5-10), mirroring exactly how
`app.trading.backtest.backtest_engine.run_backtest()` (frozen, Phase
11) already orchestrates the same chain over historical candles; this
module is that same orchestration pattern re-expressed through the
event-driven paper trading pieces (Phase 19) instead of a plain
in-memory trade list. Journal/Performance Monitor are never called
directly - both already subscribe to the event bus (Phase 19) and
learn everything from the events this module publishes.

The CTO brief's flow diagram does not name the Decision Engine as its
own box, but selecting among risk-assessed strategy candidates via
`build_trade_recommendation()` (Phase 10) is exactly that step - using
it here (rather than inlining an "if risk_ok: act" check) is reuse, not
new trading logic, and is the same reason `RiskApprovedEvent` is only
published for candidates whose risk assessment actually passed.

Exit checking (stop-loss/target/end-of-day) reapplies the same three
comparisons `app.trading.backtest.trade_executor.check_exit()` already
uses (stop-loss checked before target, same conservative assumption
about the worst intrabar path) - not reused directly, because that
function is tightly coupled to constructing a `BacktestTrade`, a
different shape from `app.paper_trading.models.Position`. Since
`Position` doesn't carry a stop-loss/target (a paper position's target
is a property of the *order* that opened it, not the position itself),
this module tracks the currently open position's stop-loss/target
internally - no change to the frozen `paper_trading` package.

SHORT order submission (a narrow, explicitly-authorized exception to
this module's own freeze - "enable BUY PE using the existing
rulebook, minimum change only"): `_evaluate_entry()`'s gate previously
required `StrategyDirection.LONG` specifically, even though the
Strategy/Risk/Decision Engines (frozen) already produce
direction-correct evaluations and stop-loss/target for SHORT, and
`PositionManager._signed_pnl()` (frozen) already flips sign for
SHORT. The gate now only excludes `StrategyDirection.NONE`.
`_check_exit()`'s intrabar breach check is the one piece that
genuinely assumed LONG (`low <= stop_loss`, `high >= target`) - now
branches on `position.direction` since SHORT's stop-loss/target sit
on the opposite side of entry. No other file in `app.runtime`,
`app.live`, or `app.paper_trading` assumed LONG-only (confirmed by
grep) - only this module's two spots needed to change.
"""

import time
import uuid
from datetime import date, datetime

from app.market_data.market_session import market_session_service
from app.market_data.schemas import Candle
from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    MarketDataReceivedEvent,
    RiskApprovedEvent,
    SignalGeneratedEvent,
)
from app.paper_trading.order_manager import OrderManager
from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager
from app.trading.conditions.engine import build_trading_conditions
from app.trading.context.engine import build_market_context
from app.trading.decision.engine import build_trade_recommendation
from app.trading.decision.models import StrategyCandidate
from app.trading.indicators.engine import calculate_indicator_snapshot
from app.trading.risk.engine import build_risk_assessment
from app.trading.risk.models import CapitalState, RiskConfig
from app.trading.strategy.engine import run_strategies
from app.trading.strategy.models import StrategyDirection
from app.trading.strategy.registry import StrategyRegistry

MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"


class EventProcessor:
    def __init__(
        self,
        *,
        event_bus: EventBus,
        order_manager: OrderManager,
        position_manager: PositionManager,
        portfolio_manager: PortfolioManager,
        broker: PaperBroker,
        strategy_registry: StrategyRegistry,
        risk_config: RiskConfig,
        initial_capital: float,
        warmup_candles: int = 20,
    ) -> None:
        self._event_bus = event_bus
        self._order_manager = order_manager
        self._position_manager = position_manager
        self._portfolio_manager = portfolio_manager
        self._broker = broker
        self._strategy_registry = strategy_registry
        self._risk_config = risk_config
        self._initial_capital = initial_capital
        self._warmup_candles = warmup_candles

        self._open_position_id: str | None = None
        self._open_position_stop_loss: float = 0.0
        self._open_position_target: float = 0.0
        self._last_trade_closed_at: datetime | None = None
        self._current_date: date | None = None
        self._trades_taken_today = 0
        self._realized_loss_today = 0.0

    def process_candle(self, candle: Candle, history: list[Candle]) -> float:
        start = time.perf_counter()

        candle_date = candle.timestamp.date()
        if candle_date != self._current_date:
            self._current_date = candle_date
            self._trades_taken_today = 0
            self._realized_loss_today = 0.0

        self._event_bus.publish(
            MarketDataReceivedEvent(
                event_id=str(uuid.uuid4()), timestamp=datetime.now(), candle=candle
            )
        )

        if len(history) <= self._warmup_candles:
            return time.perf_counter() - start

        if self._open_position_id is not None:
            self._check_exit(candle)

        if self._open_position_id is None:
            self._evaluate_entry(candle, history)

        if self._open_position_id is not None:
            self._position_manager.update_unrealized_pnl(self._open_position_id, candle.close)

        self._portfolio_manager.snapshot()

        return time.perf_counter() - start

    def _check_exit(self, candle: Candle) -> None:
        assert self._open_position_id is not None
        position = self._position_manager.get(self._open_position_id)

        # SHORT's stop-loss/target sit on the opposite side of entry from
        # LONG's (Risk Engine, frozen, already prices them that way) - the
        # intrabar breach direction flips accordingly. Stop-loss is still
        # checked before target either way, same conservative assumption.
        if position.direction == StrategyDirection.SHORT:
            stop_loss_breached = candle.high >= self._open_position_stop_loss
            target_breached = candle.low <= self._open_position_target
        else:
            stop_loss_breached = candle.low <= self._open_position_stop_loss
            target_breached = candle.high >= self._open_position_target

        exit_price: float | None = None
        if stop_loss_breached:
            exit_price = self._open_position_stop_loss
        elif target_breached:
            exit_price = self._open_position_target
        elif candle.timestamp.strftime("%H:%M") >= MARKET_CLOSE:
            exit_price = candle.close

        if exit_price is None:
            return

        closed = self._position_manager.exit(
            position.position_id, exit_quantity=position.quantity, exit_price=exit_price
        )
        realized_this_exit = closed.realized_pnl - position.realized_pnl
        self._portfolio_manager.record_cash_change(realized_this_exit)
        self._realized_loss_today += max(0.0, -realized_this_exit)
        self._last_trade_closed_at = candle.timestamp
        self._open_position_id = None

    def _evaluate_entry(self, candle: Candle, history: list[Candle]) -> None:
        snapshot = calculate_indicator_snapshot(
            history, total_call_oi=1, total_put_oi=1, price_change=0.0, oi_change=0.0
        )
        session_state = market_session_service.get_status(candle.timestamp)
        market_context = build_market_context(snapshot, session_state)
        trading_conditions = build_trading_conditions(
            session_state=session_state,
            current_timestamp=candle.timestamp,
            market_context=market_context,
            market_open=MARKET_OPEN,
            market_close=MARKET_CLOSE,
            has_open_position=False,
            last_trade_closed_at=self._last_trade_closed_at,
            volume=candle.volume,
        )

        evaluations = run_strategies(
            self._strategy_registry, snapshot, market_context, trading_conditions
        )
        for evaluation in evaluations:
            self._event_bus.publish(
                SignalGeneratedEvent(
                    event_id=str(uuid.uuid4()), timestamp=datetime.now(), evaluation=evaluation
                )
            )

        capital_state = CapitalState(
            total_capital=self._initial_capital,
            capital_deployed=0.0,
            realized_loss_today=self._realized_loss_today,
            trades_taken_today=self._trades_taken_today,
            open_positions=0,
        )

        candidates = []
        for evaluation in evaluations:
            risk_assessment = build_risk_assessment(
                strategy_evaluation=evaluation,
                entry_price=snapshot.close_price,
                atr=snapshot.atr,
                config=self._risk_config,
                capital_state=capital_state,
            )
            if risk_assessment.risk_ok:
                self._event_bus.publish(
                    RiskApprovedEvent(
                        event_id=str(uuid.uuid4()), timestamp=datetime.now(),
                        risk_assessment=risk_assessment,
                    )
                )
            candidates.append(
                StrategyCandidate(evaluation=evaluation, risk_assessment=risk_assessment)
            )

        recommendation = build_trade_recommendation(
            candidates=candidates, trading_conditions=trading_conditions
        )

        # LONG and SHORT are both submitted - the Strategy/Risk/Decision
        # Engines (frozen) already produce direction-correct evaluations,
        # stop-loss/target, and P&L for either; only NONE (no actionable
        # setup) is excluded.
        if not (
            recommendation.recommended
            and recommendation.direction != StrategyDirection.NONE
            and recommendation.risk_summary is not None
            and recommendation.risk_summary.position_size >= 1
        ):
            return

        risk_summary = recommendation.risk_summary
        order = self._order_manager.create_order(
            strategy_name=recommendation.selected_strategy or "unknown",
            direction=recommendation.direction,
            requested_price=snapshot.close_price,
            requested_quantity=risk_summary.position_size,
            stop_loss=risk_summary.stop_loss,
            target=risk_summary.target,
        )
        self._order_manager.validate(order.order_id)
        filled_order = self._order_manager.submit(order.order_id, self._broker)

        position = self._position_manager.open_position(
            strategy_name=filled_order.strategy_name,
            direction=filled_order.direction,
            entry_price=filled_order.average_fill_price or filled_order.requested_price,
            quantity=filled_order.filled_quantity,
        )
        self._open_position_id = position.position_id
        self._open_position_stop_loss = risk_summary.stop_loss
        self._open_position_target = risk_summary.target
        self._trades_taken_today += 1

    @property
    def has_open_position(self) -> bool:
        return self._open_position_id is not None
