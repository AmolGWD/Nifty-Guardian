from app.trading.conditions.position_guard import is_position_guard_ok


def test_position_guard_ok_when_no_open_position() -> None:
    assert is_position_guard_ok(False) is True


def test_position_guard_blocks_when_position_already_open() -> None:
    assert is_position_guard_ok(True) is False
