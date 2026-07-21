"""
Option Chain Bias: standard Put-Call-Ratio interpretation (PCR > 1
skews bullish, heavy put writing suggests support; PCR < 1 skews
bearish, heavy call writing suggests resistance), confirmed by the
Open Interest signal pointing the same direction.
"""

from app.trading.context.models import Bias
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.indicators.open_interest import OpenInterestSignal

_BULLISH_PCR_THRESHOLD = 1.2
_BEARISH_PCR_THRESHOLD = 0.8

_BULLISH_OI_SIGNALS = (OpenInterestSignal.LONG_BUILDUP, OpenInterestSignal.SHORT_COVERING)
_BEARISH_OI_SIGNALS = (OpenInterestSignal.SHORT_BUILDUP, OpenInterestSignal.LONG_UNWINDING)


def classify_option_chain_bias(snapshot: IndicatorSnapshot) -> Bias:
    if snapshot.put_call_ratio > _BULLISH_PCR_THRESHOLD and (
        snapshot.open_interest_signal in _BULLISH_OI_SIGNALS
    ):
        return Bias.BULLISH_BIAS

    if snapshot.put_call_ratio < _BEARISH_PCR_THRESHOLD and (
        snapshot.open_interest_signal in _BEARISH_OI_SIGNALS
    ):
        return Bias.BEARISH_BIAS

    return Bias.NEUTRAL_BIAS
