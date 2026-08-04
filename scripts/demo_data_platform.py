#!/usr/bin/env python3
"""
Standalone demonstration of the Historical Data Platform.

Imports the same sample CSV used by the other demo scripts, validates
it, stores it, queries a date range, and prints the resulting
statistics and validation report.

Requires no Zerodha credentials, no network access, and no FastAPI
server. Run from anywhere:

    python3 scripts/demo_data_platform.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.data.cache.cache_manager import CacheManager  # noqa: E402
from app.data.models import DatasetKey, Exchange, Instrument, Timeframe  # noqa: E402
from app.data.providers.csv_provider import CSVHistoricalDataProvider  # noqa: E402
from app.data.repository import DatasetValidationError, HistoricalDataRepository  # noqa: E402
from app.data.services.import_service import ImportService  # noqa: E402
from app.data.services.query_service import QueryService  # noqa: E402

SAMPLE_CSV = _BACKEND_DIR / "app" / "market_data" / "sample_data" / "nifty_sample_candles.csv"


def _print_header(title: str) -> None:
    banner = "=" * 33
    print(f"\n{banner}")
    print(title)
    print(banner)


def main() -> None:
    repository = HistoricalDataRepository()
    cache = CacheManager()
    import_service = ImportService(repository, cache)
    query_service = QueryService(repository, cache)

    instrument = Instrument(
        symbol="NIFTY",
        exchange=Exchange.NSE,
        timeframe=Timeframe.FIFTEEN_MINUTE,
        name="Nifty 50",
        lot_size=75,
    )
    provider = CSVHistoricalDataProvider(SAMPLE_CSV)

    _print_header("IMPORT CSV")
    print(f"Source: {SAMPLE_CSV.name}")
    print(f"Instrument: {instrument.symbol} ({instrument.exchange.value}, "
          f"{instrument.timeframe.value})")

    # Deliberately force=True: this demo's point is to show the
    # validation report even if the sample data happens to trip an
    # anomaly threshold - a real import would inspect the report
    # first and decide whether force=True is actually appropriate.
    report = import_service.import_from_provider(
        provider, instrument, datetime(2000, 1, 1), datetime(2100, 1, 1), force=True
    )

    _print_header("VALIDATE DATASET")
    print(f"Total candles checked: {report.total_candles}")
    print(f"Valid: {report.is_valid}")
    print(f"Issues found: {len(report.issues)}")

    _print_header("STORE DATASET")
    key = DatasetKey(
        symbol=instrument.symbol, exchange=instrument.exchange, timeframe=instrument.timeframe
    )
    stored = query_service.get_instrument_metadata(key)
    print(f"Stored instrument metadata: {stored}")

    _print_header("QUERY ONE MONTH")
    month_start = datetime(2026, 7, 1)
    month_end = datetime(2026, 7, 31, 23, 59, 59)
    month_candles = query_service.get_date_range(key, month_start, month_end)
    print(f"Candles found in {month_start.date()} - {month_end.date()}: {len(month_candles)}")
    if month_candles:
        print(f"First: {month_candles[0].timestamp} close={month_candles[0].close}")
        print(f"Last:  {month_candles[-1].timestamp} close={month_candles[-1].close}")

    _print_header("STATISTICS")
    stats = query_service.get_statistics(key)
    if stats is not None:
        print(f"Candle count:    {stats.candle_count}")
        print(f"First timestamp: {stats.first_timestamp}")
        print(f"Last timestamp:  {stats.last_timestamp}")
        print(f"Min close:       {stats.min_close}")
        print(f"Max close:       {stats.max_close}")
        print(f"Average volume:  {stats.average_volume:,.2f}" if stats.average_volume else "N/A")

    _print_header("VALIDATION REPORT")
    if report.is_valid:
        print("No issues found.")
    else:
        for issue in report.issues:
            print(f"  [{issue.issue_type.value}] {issue.timestamp}: {issue.detail}")


if __name__ == "__main__":
    try:
        main()
    except DatasetValidationError as error:
        print(f"Import rejected: {error}")
