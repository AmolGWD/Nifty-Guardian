from datetime import datetime

from app.trading.analytics.drawdown import identify_drawdown_episodes
from tests.trading.analytics.helpers import make_equity_point


def test_identifies_a_single_recovered_episode() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 11, 0), equity=105_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 12, 0), equity=98_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 13, 0), equity=101_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 14, 0), equity=105_000.0),
    ]

    episodes = identify_drawdown_episodes(curve)

    assert len(episodes) == 1
    episode = episodes[0]
    assert episode.peak_time == datetime(2026, 7, 21, 11, 0)
    assert episode.trough_time == datetime(2026, 7, 21, 12, 0)
    assert episode.recovery_time == datetime(2026, 7, 21, 14, 0)
    assert episode.depth == 7_000.0
    assert round(episode.depth_percent, 4) == round(7_000.0 / 105_000.0 * 100, 4)


def test_ongoing_episode_at_end_of_data_has_no_recovery_time() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 11, 0), equity=90_000.0),
    ]

    episodes = identify_drawdown_episodes(curve)

    assert len(episodes) == 1
    assert episodes[0].recovery_time is None


def test_no_episodes_when_equity_only_rises() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 11, 0), equity=101_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 12, 0), equity=102_000.0),
    ]

    assert identify_drawdown_episodes(curve) == []


def test_empty_curve_produces_no_episodes() -> None:
    assert identify_drawdown_episodes([]) == []


def test_two_distinct_episodes_are_both_identified() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 9, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0), equity=95_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 11, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 12, 0), equity=110_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 13, 0), equity=104_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 14, 0), equity=110_000.0),
    ]

    episodes = identify_drawdown_episodes(curve)

    assert len(episodes) == 2
    assert episodes[0].depth == 5_000.0
    assert episodes[1].depth == 6_000.0
