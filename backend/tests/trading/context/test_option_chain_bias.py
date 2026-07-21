from app.trading.context.models import Bias
from app.trading.context.option_chain_bias import classify_option_chain_bias
from app.trading.indicators.open_interest import OpenInterestSignal
from tests.trading.context.helpers import make_snapshot


def test_bullish_requires_high_pcr_and_confirming_oi() -> None:
    snapshot = make_snapshot(
        put_call_ratio=1.5, open_interest_signal=OpenInterestSignal.LONG_BUILDUP
    )
    assert classify_option_chain_bias(snapshot) == Bias.BULLISH_BIAS


def test_bearish_requires_low_pcr_and_confirming_oi() -> None:
    snapshot = make_snapshot(
        put_call_ratio=0.5, open_interest_signal=OpenInterestSignal.SHORT_BUILDUP
    )
    assert classify_option_chain_bias(snapshot) == Bias.BEARISH_BIAS


def test_high_pcr_without_confirming_oi_is_neutral() -> None:
    snapshot = make_snapshot(
        put_call_ratio=1.5, open_interest_signal=OpenInterestSignal.SHORT_BUILDUP
    )
    assert classify_option_chain_bias(snapshot) == Bias.NEUTRAL_BIAS


def test_pcr_near_one_is_neutral() -> None:
    snapshot = make_snapshot(
        put_call_ratio=1.0, open_interest_signal=OpenInterestSignal.LONG_BUILDUP
    )
    assert classify_option_chain_bias(snapshot) == Bias.NEUTRAL_BIAS
