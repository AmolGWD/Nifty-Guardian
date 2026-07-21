"""
Statistical anomaly detection - abnormal single-candle price moves and
abnormal volume - kept separate from `validator.py`'s mechanical,
purely-structural checks (missing/duplicate/out-of-order timestamps,
negative values, OHLC consistency), since these are threshold-based
judgment calls rather than hard structural rules.
"""

from app.data.models import OHLCVRecord, ValidationIssue, ValidationIssueType

_DEFAULT_PRICE_MOVE_THRESHOLD_PERCENT = 20.0
_DEFAULT_VOLUME_Z_SCORE_THRESHOLD = 5.0


def detect_abnormal_price_moves(
    candles: list[OHLCVRecord],
    *,
    threshold_percent: float = _DEFAULT_PRICE_MOVE_THRESHOLD_PERCENT,
) -> list[ValidationIssue]:
    issues = []

    for i in range(1, len(candles)):
        previous_close = candles[i - 1].close
        if previous_close == 0:
            continue

        move_percent = abs(candles[i].close - previous_close) / previous_close * 100
        if move_percent > threshold_percent:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.ABNORMAL_PRICE_MOVE,
                    timestamp=candles[i].timestamp,
                    detail=f"{move_percent:.2f}% move from previous close ({previous_close})",
                )
            )

    return issues


def detect_abnormal_volume(
    candles: list[OHLCVRecord],
    *,
    z_score_threshold: float = _DEFAULT_VOLUME_Z_SCORE_THRESHOLD,
) -> list[ValidationIssue]:
    if len(candles) < 2:
        return []

    volumes = [candle.volume for candle in candles]
    mean_volume = sum(volumes) / len(volumes)
    variance = sum((volume - mean_volume) ** 2 for volume in volumes) / len(volumes)
    std_dev = variance**0.5
    if std_dev == 0:
        return []

    issues = []
    for candle in candles:
        z_score = (candle.volume - mean_volume) / std_dev
        if abs(z_score) > z_score_threshold:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.ABNORMAL_VOLUME,
                    timestamp=candle.timestamp,
                    detail=f"volume {candle.volume} has z-score {z_score:.2f}",
                )
            )

    return issues
