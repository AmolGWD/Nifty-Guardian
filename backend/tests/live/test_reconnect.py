from app.live.reconnect import ReconnectManager, ReconnectPolicy


def _no_sleep(_seconds: float) -> None:
    return None


def test_next_delay_grows_exponentially_up_to_the_cap() -> None:
    policy = ReconnectPolicy(max_retries=5, base_delay_seconds=1.0, max_delay_seconds=10.0)
    assert policy.next_delay(0) == 1.0
    assert policy.next_delay(1) == 2.0
    assert policy.next_delay(2) == 4.0
    assert policy.next_delay(3) == 8.0
    assert policy.next_delay(4) == 10.0  # capped: 1 * 2^4 = 16, capped to 10


def test_reconnect_succeeds_on_first_attempt() -> None:
    policy = ReconnectPolicy(max_retries=3, base_delay_seconds=1.0)
    manager = ReconnectManager(policy, sleep_fn=_no_sleep)

    outcome = manager.reconnect(lambda: True)

    assert outcome.succeeded is True
    assert outcome.attempts == 1
    assert outcome.total_delay_seconds == 1.0


def test_reconnect_succeeds_after_several_failed_attempts() -> None:
    policy = ReconnectPolicy(max_retries=5, base_delay_seconds=1.0)
    manager = ReconnectManager(policy, sleep_fn=_no_sleep)
    calls = {"count": 0}

    def _attempt() -> bool:
        calls["count"] += 1
        return calls["count"] == 3

    outcome = manager.reconnect(_attempt)

    assert outcome.succeeded is True
    assert outcome.attempts == 3
    assert outcome.total_delay_seconds == 1.0 + 2.0 + 4.0


def test_reconnect_reports_failure_after_exhausting_max_retries() -> None:
    policy = ReconnectPolicy(max_retries=3, base_delay_seconds=1.0)
    manager = ReconnectManager(policy, sleep_fn=_no_sleep)

    outcome = manager.reconnect(lambda: False)

    assert outcome.succeeded is False
    assert outcome.attempts == 3
    assert outcome.total_delay_seconds == 1.0 + 2.0 + 4.0


def test_sleep_fn_is_called_before_each_connect_attempt() -> None:
    policy = ReconnectPolicy(max_retries=2, base_delay_seconds=1.0)
    sleeps: list[float] = []
    manager = ReconnectManager(policy, sleep_fn=sleeps.append)

    manager.reconnect(lambda: False)

    assert sleeps == [1.0, 2.0]
