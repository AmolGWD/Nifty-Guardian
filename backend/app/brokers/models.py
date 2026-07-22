"""
This adapter's own domain types for broker-side read data that has no
existing equivalent anywhere in this codebase.

`app.paper_trading.models.Order` is reused directly (not redefined
here) for `BrokerInterface.submit_order()`/`cancel_order()` - that
Protocol already mandates it. A live broker *position*, however, is a
different concept from `app.paper_trading.models.Position`: the latter
is a stateful value `PositionManager` owns and transitions through
`OPEN`/`PARTIALLY_EXITED`/`CLOSED` for one paper strategy's trade - it
has no `strategy_name`/status-transition-table equivalent in what
Zerodha's API actually returns, and a live position query has fields
(`product`, `last_price`, exchange) paper trading has no use for. A
broker "holding" (long-term stock/ETF holdings, distinct from an
intraday/derivatives position) has no existing type at all. Both are
new, read-only value types this adapter alone owns.
"""

from pydantic import BaseModel, ConfigDict


class BrokerOrder(BaseModel):
    """
    Raw shape of one order as Zerodha's API returns it - used only as
    an intermediate step before `mapper.py` merges it onto the
    original internal `Order` (see that module's docstring for why a
    full round-trip into `Order` alone isn't possible: `strategy_name`/
    `stop_loss`/`target` are this codebase's own fields, not
    Zerodha's).
    """

    model_config = ConfigDict(frozen=True)

    order_id: str
    status: str
    quantity: int
    filled_quantity: int
    average_price: float | None
    transaction_type: str


class BrokerPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    trading_symbol: str
    exchange: str
    product: str
    quantity: int
    average_price: float
    last_price: float
    pnl: float


class BrokerHolding(BaseModel):
    model_config = ConfigDict(frozen=True)

    trading_symbol: str
    exchange: str
    isin: str
    quantity: int
    average_price: float
    last_price: float
    pnl: float


class BrokerProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str
    user_name: str
    email: str
    broker: str
