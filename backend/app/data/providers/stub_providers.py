"""
Future provider interfaces - structurally conform to
`HistoricalDataProvider` (matching `fetch()` signature) so a future
implementation is a drop-in, but every one raises `NotImplementedError`
here. No network access, no broker/vendor SDK import anywhere in this
file - per this phase's explicit "do not implement network access yet".
"""

from datetime import datetime

from app.data.models import OHLCVRecord


class KiteHistoricalProvider:
    def fetch(self, start: datetime, end: datetime) -> list[OHLCVRecord]:
        raise NotImplementedError(
            "KiteHistoricalProvider is an interface only - no network access implemented yet"
        )


class YahooHistoricalProvider:
    def fetch(self, start: datetime, end: datetime) -> list[OHLCVRecord]:
        raise NotImplementedError(
            "YahooHistoricalProvider is an interface only - no network access implemented yet"
        )


class PolygonHistoricalProvider:
    def fetch(self, start: datetime, end: datetime) -> list[OHLCVRecord]:
        raise NotImplementedError(
            "PolygonHistoricalProvider is an interface only - no network access implemented yet"
        )


class NSEHistoricalProvider:
    def fetch(self, start: datetime, end: datetime) -> list[OHLCVRecord]:
        raise NotImplementedError(
            "NSEHistoricalProvider is an interface only - no network access implemented yet"
        )
