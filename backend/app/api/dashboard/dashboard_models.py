"""
Response models for GET /api/dashboard and GET /api/runtime/*.

Every field re-exposes an existing, already-approved frozen domain
model directly (`Candle`, `MarketContext`, `StrategyEvaluation`,
`RiskAssessment`, `TradeRecommendation`, `Order`, `Position`,
`Portfolio`, `JournalEntry`, `HealthSnapshot`, `PerformanceSnapshot`) -
this module defines exactly one new type, `RuntimeStatsResponse`,
because no single frozen model already bundles replay speed + total
candle count alongside `HealthSnapshot`'s processed-candles/events/
uptime/state fields.
"""

from pydantic import BaseModel, ConfigDict, computed_field

from app.market_data.schemas import Candle
from app.paper_trading.execution_journal import JournalEntry
from app.paper_trading.models import Order, Portfolio, Position
from app.paper_trading.performance_monitor import PerformanceSnapshot
from app.runtime.engine_config import ReplaySpeed
from app.runtime.health import HealthSnapshot
from app.runtime.session_controller import SessionState
from app.trading.context.models import MarketContext
from app.trading.decision.models import TradeRecommendation
from app.trading.risk.models import RiskAssessment
from app.trading.strategy.models import StrategyEvaluation


class PortfolioResponse(Portfolio):
    """
    `Portfolio` (frozen, app.paper_trading.models) re-declared here with
    `drawdown`/`drawdown_percent` promoted from plain `@property` to
    `@computed_field @property`.

    This is a real, previously-latent gap in the frozen model: Pydantic
    v2 (and therefore FastAPI's JSON response serialization) silently
    omits plain `@property` methods from `model_dump()`/JSON output -
    only declared fields and `@computed_field`-decorated properties
    serialize. `Portfolio.drawdown`/`drawdown_percent` were invisible to
    any JSON consumer, including this very API, even though the frozen
    `PortfolioPanel` (Phase 21) already renders both. No REST endpoint
    existed before this phase to expose it. Fixed here, as a subclass in
    this new, unfrozen module, rather than editing app.paper_trading.
    models itself - the formula is reused via `super().drawdown`/
    `super().drawdown_percent`, not duplicated.
    """

    model_config = ConfigDict(frozen=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def drawdown(self) -> float:
        return super().drawdown

    @computed_field  # type: ignore[prop-decorator]
    @property
    def drawdown_percent(self) -> float:
        return super().drawdown_percent


class RuntimeStatsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    session_state: SessionState
    replay_speed: ReplaySpeed
    processed_candles: int
    total_candles: int
    events_published: int
    orders_generated: int
    uptime_seconds: float


class DashboardSnapshotResponse(BaseModel):
    """
    Mirrors `frontend/src/types/dashboard.ts`'s `DashboardSnapshot`
    exactly, field for field - `RestDashboardService` (frontend) maps
    this response's snake_case fields into that camelCase shape.

    `latest_recommendation` is always `null` this phase: no event on
    `app.paper_trading.event_bus.EventBus` (frozen) carries a
    `TradeRecommendation` - `EventProcessor._evaluate_entry()` (frozen,
    app.runtime) computes one internally via `build_trade_recommendation()`
    but only acts on it, never publishes it. Recomputing it independently
    in this API layer would mean re-running the Strategy/Risk/Decision
    pipeline a second time outside the package that owns it - exactly
    the "new trading logic" this whole engagement has avoided - so this
    is an honest, documented gap rather than a duplicated computation.
    `latest_risk_decision` has a narrower, but real, version of the same
    limitation: `RiskApprovedEvent` (frozen) is only published when
    `risk_ok` is `True`, so a risk-rejected evaluation leaves this field
    showing whatever the last *approved* assessment was, not "rejected."
    """

    model_config = ConfigDict(frozen=True)

    runtime: RuntimeStatsResponse
    current_candle: Candle | None
    market_context: MarketContext | None
    latest_signal: StrategyEvaluation | None
    latest_risk_decision: RiskAssessment | None
    latest_recommendation: TradeRecommendation | None
    orders: list[Order]
    positions: list[Position]
    portfolio: PortfolioResponse
    journal: list[JournalEntry]
    health: HealthSnapshot
    performance: PerformanceSnapshot
