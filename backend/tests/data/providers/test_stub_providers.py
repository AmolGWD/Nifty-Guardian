from datetime import datetime

import pytest

from app.data.providers.stub_providers import (
    KiteHistoricalProvider,
    NSEHistoricalProvider,
    PolygonHistoricalProvider,
    YahooHistoricalProvider,
)

_START = datetime(2026, 7, 21)
_END = datetime(2026, 7, 22)


@pytest.mark.parametrize(
    "provider",
    [
        KiteHistoricalProvider(),
        YahooHistoricalProvider(),
        PolygonHistoricalProvider(),
        NSEHistoricalProvider(),
    ],
)
def test_stub_providers_raise_not_implemented(provider: object) -> None:
    with pytest.raises(NotImplementedError):
        provider.fetch(_START, _END)  # type: ignore[attr-defined]
