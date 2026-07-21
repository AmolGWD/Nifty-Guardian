from datetime import UTC, datetime

from app.data.models import Timeframe, ValidationIssueType
from app.data.validation.validator import validate_dataset
from tests.data.helpers import make_clean_series, make_key, make_record


def test_valid_clean_series_produces_no_issues() -> None:
    candles = make_clean_series(20)

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    assert report.is_valid is True
    assert report.total_candles == 20


def test_detects_duplicate_timestamps() -> None:
    timestamp = datetime(2026, 7, 21, 9, 15)
    candles = [make_record(timestamp=timestamp), make_record(timestamp=timestamp)]

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.DUPLICATE_TIMESTAMP in issue_types


def test_detects_out_of_order_candles() -> None:
    candles = [
        make_record(timestamp=datetime(2026, 7, 21, 9, 30)),
        make_record(timestamp=datetime(2026, 7, 21, 9, 15)),
    ]

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.OUT_OF_ORDER in issue_types


def test_detects_negative_price() -> None:
    candles = [make_record(open=-1.0)]

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.NEGATIVE_PRICE in issue_types


def test_detects_negative_volume() -> None:
    candles = [make_record(volume=-100)]

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.NEGATIVE_VOLUME in issue_types


def test_detects_high_below_open_or_close() -> None:
    candles = [make_record(open=100.0, high=99.0, low=95.0, close=98.0)]

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.HIGH_BELOW_OPEN_OR_CLOSE in issue_types


def test_detects_low_above_open_or_close() -> None:
    candles = [make_record(open=100.0, high=105.0, low=101.0, close=98.0)]

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.LOW_ABOVE_OPEN_OR_CLOSE in issue_types


def test_detects_timezone_inconsistency() -> None:
    candles = [
        make_record(timestamp=datetime(2026, 7, 21, 9, 15)),
        make_record(timestamp=datetime(2026, 7, 21, 9, 30, tzinfo=UTC)),
    ]

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.TIMEZONE_INCONSISTENT in issue_types


def test_detects_missing_candle_within_the_same_day() -> None:
    candles = [
        make_record(timestamp=datetime(2026, 7, 21, 9, 15)),
        make_record(timestamp=datetime(2026, 7, 21, 9, 30)),
        make_record(timestamp=datetime(2026, 7, 21, 10, 15)),  # gap - missing 9:45, 10:00
    ]

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.MISSING_CANDLE in issue_types


def test_no_missing_candle_flagged_across_different_days() -> None:
    candles = [
        make_record(timestamp=datetime(2026, 7, 21, 15, 15)),
        make_record(timestamp=datetime(2026, 7, 22, 9, 15)),
    ]

    report = validate_dataset(make_key(), candles, Timeframe.FIFTEEN_MINUTE)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.MISSING_CANDLE not in issue_types


def test_missing_candle_check_is_skipped_for_daily_timeframe() -> None:
    candles = [
        make_record(timestamp=datetime(2026, 7, 21, 0, 0)),
        make_record(timestamp=datetime(2026, 7, 30, 0, 0)),  # a huge gap, but daily timeframe
    ]

    report = validate_dataset(make_key(), candles, Timeframe.ONE_DAY)

    issue_types = {issue.issue_type for issue in report.issues}
    assert ValidationIssueType.MISSING_CANDLE not in issue_types


def test_empty_dataset_is_valid() -> None:
    report = validate_dataset(make_key(), [], Timeframe.FIFTEEN_MINUTE)

    assert report.is_valid is True
    assert report.total_candles == 0
