from datetime import datetime, timedelta

from app.data.models import ValidationIssueType
from app.data.validation.anomalies import detect_abnormal_price_moves, detect_abnormal_volume
from tests.data.helpers import make_record


def test_detect_abnormal_price_moves_flags_a_large_jump() -> None:
    candles = [
        make_record(timestamp=datetime(2026, 7, 21, 9, 15), close=100.0),
        make_record(timestamp=datetime(2026, 7, 21, 9, 30), close=150.0),  # +50%
    ]

    issues = detect_abnormal_price_moves(candles, threshold_percent=20.0)

    assert len(issues) == 1
    assert issues[0].issue_type == ValidationIssueType.ABNORMAL_PRICE_MOVE


def test_detect_abnormal_price_moves_ignores_normal_moves() -> None:
    candles = [
        make_record(timestamp=datetime(2026, 7, 21, 9, 15), close=100.0),
        make_record(timestamp=datetime(2026, 7, 21, 9, 30), close=101.0),
    ]

    assert detect_abnormal_price_moves(candles, threshold_percent=20.0) == []


def test_detect_abnormal_volume_flags_a_spike() -> None:
    # With a single outlier among N points, the population z-score of
    # that outlier can never exceed sqrt(N-1) no matter how extreme the
    # outlier is - so this needs enough "normal" points (40) for a
    # spike to actually clear the default z_score_threshold of 5.0
    # (sqrt(40) ~= 6.32 gives enough headroom).
    timestamp = datetime(2026, 7, 21, 9, 15)
    candles = [
        make_record(timestamp=timestamp + timedelta(minutes=15 * i), volume=1000)
        for i in range(40)
    ]
    candles.append(make_record(timestamp=timestamp + timedelta(minutes=15 * 40), volume=50_000))

    issues = detect_abnormal_volume(candles)

    assert len(issues) == 1
    assert issues[0].issue_type == ValidationIssueType.ABNORMAL_VOLUME


def test_detect_abnormal_volume_returns_empty_with_uniform_volume() -> None:
    timestamp = datetime(2026, 7, 21, 9, 15)
    candles = [
        make_record(timestamp=timestamp + timedelta(minutes=15 * i), volume=1000)
        for i in range(10)
    ]

    assert detect_abnormal_volume(candles) == []


def test_detect_abnormal_volume_returns_empty_with_fewer_than_two_candles() -> None:
    assert detect_abnormal_volume([make_record()]) == []
    assert detect_abnormal_volume([]) == []
