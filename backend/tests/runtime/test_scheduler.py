from app.runtime.scheduler import SynchronousScheduler


def test_runs_until_step_returns_false() -> None:
    calls = {"n": 0}

    def step() -> bool:
        calls["n"] += 1
        return calls["n"] < 5

    SynchronousScheduler(sleep_fn=lambda seconds: None).run(step, delay_seconds=0.0)
    assert calls["n"] == 5


def test_stops_immediately_if_step_returns_false_first_call() -> None:
    calls = {"n": 0}

    def step() -> bool:
        calls["n"] += 1
        return False

    SynchronousScheduler(sleep_fn=lambda seconds: None).run(step, delay_seconds=0.0)
    assert calls["n"] == 1


def test_sleeps_between_steps_when_delay_positive() -> None:
    sleep_calls: list[float] = []
    calls = {"n": 0}

    def step() -> bool:
        calls["n"] += 1
        return calls["n"] < 3

    SynchronousScheduler(sleep_fn=sleep_calls.append).run(step, delay_seconds=0.5)
    assert sleep_calls == [0.5, 0.5]


def test_does_not_sleep_when_delay_zero() -> None:
    sleep_calls: list[float] = []

    def step() -> bool:
        return False

    SynchronousScheduler(sleep_fn=sleep_calls.append).run(step, delay_seconds=0.0)
    assert sleep_calls == []


def test_default_sleep_fn_is_time_sleep() -> None:
    scheduler = SynchronousScheduler()
    assert scheduler._sleep_fn is not None
