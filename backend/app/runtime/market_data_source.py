"""
MarketDataSource: where the engine's candles come from. Two
implementations this phase, both purely in-memory/file-based - no
websocket, no Zerodha, no REST API anywhere in this module (a future
live source would be a third implementation of the same `Protocol`,
the same seam `app.paper_trading.broker_interface.BrokerInterface`
already established for brokers).

`HistoricalReplaySource` loads a CSV via the existing (frozen)
`app.trading.backtest.loader.load_candles_from_csv` - no CSV parsing
is reimplemented here. `StaticListSource` wraps an already-in-memory
`list[Candle]` directly (what `scripts/demo_runtime_engine.py` and
most tests use, to avoid a real file).
"""

from collections.abc import Iterator
from typing import Protocol

from app.market_data.schemas import Candle
from app.trading.backtest.loader import load_candles_from_csv


class MarketDataSource(Protocol):
    def __iter__(self) -> Iterator[Candle]: ...

    def __len__(self) -> int: ...


class StaticListSource:
    def __init__(self, candles: list[Candle], *, maximum_candles: int | None = None) -> None:
        self._candles = candles if maximum_candles is None else candles[:maximum_candles]

    def __iter__(self) -> Iterator[Candle]:
        return iter(self._candles)

    def __len__(self) -> int:
        return len(self._candles)


class HistoricalReplaySource:
    def __init__(self, dataset_path: str, *, maximum_candles: int | None = None) -> None:
        candles = load_candles_from_csv(dataset_path)
        self._candles = candles if maximum_candles is None else candles[:maximum_candles]

    def __iter__(self) -> Iterator[Candle]:
        return iter(self._candles)

    def __len__(self) -> int:
        return len(self._candles)
