from app.trading.conditions.liquidity import is_liquidity_ok


def test_liquidity_ok_when_no_volume_supplied() -> None:
    assert is_liquidity_ok(None, 500) is True


def test_liquidity_ok_when_volume_meets_minimum() -> None:
    assert is_liquidity_ok(500, 500) is True


def test_liquidity_ok_when_volume_exceeds_minimum() -> None:
    assert is_liquidity_ok(1000, 500) is True


def test_liquidity_blocks_when_volume_below_minimum() -> None:
    assert is_liquidity_ok(100, 500) is False
