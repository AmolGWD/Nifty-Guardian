"""
Structural validation of an imported dataset: missing candles,
duplicate timestamps, out-of-order candles, negative prices/volume,
OHLC consistency, and timezone consistency - plus the statistical
anomaly checks from `anomalies.py`. Produces one ValidationReport,
never raises - the caller (the repository) decides what to do with
issues.

Missing-candle detection only checks gaps *within* the same calendar
date - a gap between the last candle of one day and the first of the
next is expected (markets close overnight), not missing data, and
there is no exchange holiday calendar available to reason about
multi-day gaps more precisely (the same limitation already flagged for
`app.market_data.market_session` since Phase 4). Daily-timeframe
datasets skip this check entirely, since "missing candle" isn't a
minute-interval concept at that resolution.
"""

from datetime import UTC, datetime

from app.data.models import (
    DatasetKey,
    OHLCVRecord,
    Timeframe,
    ValidationIssue,
    ValidationIssueType,
    ValidationReport,
)
from app.data.validation.anomalies import detect_abnormal_price_moves, detect_abnormal_volume

_TIMEFRAME_MINUTES: dict[Timeframe, int] = {
    Timeframe.ONE_MINUTE: 1,
    Timeframe.THREE_MINUTE: 3,
    Timeframe.FIVE_MINUTE: 5,
    Timeframe.FIFTEEN_MINUTE: 15,
    Timeframe.THIRTY_MINUTE: 30,
    Timeframe.ONE_HOUR: 60,
}


def validate_dataset(
    key: DatasetKey, candles: list[OHLCVRecord], timeframe: Timeframe
) -> ValidationReport:
    issues: list[ValidationIssue] = []

    issues.extend(_detect_duplicates(candles))
    issues.extend(_detect_out_of_order(candles))
    issues.extend(_detect_negative_values(candles))
    issues.extend(_detect_ohlc_inconsistency(candles))
    issues.extend(_detect_timezone_inconsistency(candles))
    issues.extend(_detect_missing_candles(candles, timeframe))
    issues.extend(detect_abnormal_price_moves(candles))
    issues.extend(detect_abnormal_volume(candles))

    return ValidationReport(key=key, total_candles=len(candles), issues=tuple(issues))


def _comparable(timestamp: datetime) -> datetime:
    """
    Normalizes a timestamp for ordering/gap comparisons only (never for
    the value reported in an issue) - Python raises TypeError comparing
    a naive and an aware datetime directly, which would otherwise crash
    validation on exactly the kind of mixed-timezone dataset
    `_detect_timezone_inconsistency` exists to flag. Aware timestamps
    are converted to naive UTC; naive ones are left as-is, consistent
    with this codebase's convention of treating naive datetimes as
    already being in a fixed reference (IST) - see `_time_utils.as_ist()`
    in `app.trading.conditions`.
    """
    if timestamp.tzinfo is None:
        return timestamp
    return timestamp.astimezone(UTC).replace(tzinfo=None)


def _detect_duplicates(candles: list[OHLCVRecord]) -> list[ValidationIssue]:
    seen: set[datetime] = set()
    issues = []
    for candle in candles:
        if candle.timestamp in seen:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.DUPLICATE_TIMESTAMP,
                    timestamp=candle.timestamp,
                    detail=f"timestamp {candle.timestamp} appears more than once",
                )
            )
        seen.add(candle.timestamp)
    return issues


def _detect_out_of_order(candles: list[OHLCVRecord]) -> list[ValidationIssue]:
    issues = []
    for i in range(1, len(candles)):
        if _comparable(candles[i].timestamp) < _comparable(candles[i - 1].timestamp):
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.OUT_OF_ORDER,
                    timestamp=candles[i].timestamp,
                    detail=f"{candles[i].timestamp} comes after {candles[i - 1].timestamp}",
                )
            )
    return issues


def _detect_negative_values(candles: list[OHLCVRecord]) -> list[ValidationIssue]:
    issues = []
    for candle in candles:
        if candle.open < 0 or candle.high < 0 or candle.low < 0 or candle.close < 0:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.NEGATIVE_PRICE,
                    timestamp=candle.timestamp,
                    detail="one or more OHLC values is negative",
                )
            )
        if candle.volume < 0:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.NEGATIVE_VOLUME,
                    timestamp=candle.timestamp,
                    detail=f"volume {candle.volume} is negative",
                )
            )
    return issues


def _detect_ohlc_inconsistency(candles: list[OHLCVRecord]) -> list[ValidationIssue]:
    issues = []
    for candle in candles:
        if candle.high < candle.open or candle.high < candle.close or candle.high < candle.low:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.HIGH_BELOW_OPEN_OR_CLOSE,
                    timestamp=candle.timestamp,
                    detail=(
                        f"high={candle.high} below open={candle.open}/"
                        f"close={candle.close}/low={candle.low}"
                    ),
                )
            )
        if candle.low > candle.open or candle.low > candle.close or candle.low > candle.high:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.LOW_ABOVE_OPEN_OR_CLOSE,
                    timestamp=candle.timestamp,
                    detail=(
                        f"low={candle.low} above open={candle.open}/"
                        f"close={candle.close}/high={candle.high}"
                    ),
                )
            )
    return issues


def _detect_timezone_inconsistency(candles: list[OHLCVRecord]) -> list[ValidationIssue]:
    offsets = {candle.timestamp.utcoffset() for candle in candles}
    if len(offsets) > 1:
        return [
            ValidationIssue(
                issue_type=ValidationIssueType.TIMEZONE_INCONSISTENT,
                timestamp=None,
                detail=(
                    f"dataset mixes {len(offsets)} distinct UTC offsets: "
                    f"{sorted(offsets, key=str)}"
                ),
            )
        ]
    return []


def _detect_missing_candles(
    candles: list[OHLCVRecord], timeframe: Timeframe
) -> list[ValidationIssue]:
    expected_minutes = _TIMEFRAME_MINUTES.get(timeframe)
    if expected_minutes is None:
        return []

    issues = []
    for i in range(1, len(candles)):
        previous, current = candles[i - 1], candles[i]
        previous_ts, current_ts = _comparable(previous.timestamp), _comparable(current.timestamp)
        if previous_ts.date() != current_ts.date():
            continue

        gap_minutes = (current_ts - previous_ts).total_seconds() / 60
        if gap_minutes > expected_minutes:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.MISSING_CANDLE,
                    timestamp=current.timestamp,
                    detail=(
                        f"gap of {gap_minutes:.0f} minutes since {previous.timestamp} "
                        f"(expected {expected_minutes})"
                    ),
                )
            )
    return issues
