"""
EMA Breakout Strategy - the trading rules previously used for NIFTY
Guardian's breakout signal, adapted to a symmetric bullish/bearish
design: price vs EMA, RSI vs a bullish/bearish threshold pair, price vs
VWAP, and SuperTrend's own direction, corroborated by the Market
Context Engine's Trend classification.

The original rule set (see the pre-rebuild `debug/signal-runtime`
branch's `indicator_service.py`/`rule_engine.py`) was long-only: it
checked "price > EMA16", "RSI > 55", "price > VWAP", and SuperTrend
bullish, then converted a weighted pass count into a 0-100 confidence
score. This phase forbids both BUY/SELL decisions and confidence
scoring, so this strategy instead:

- Evaluates each of the five checks independently as
  Long/Short/Neutral, keeping the original bullish RSI threshold (55)
  and adding a symmetric bearish threshold (45) so the same rule set
  can recognize breakouts in either direction, not just long.
- Reports `direction` as whichever side has more agreeing checks.
- Reports `strength` as a categorical read of how many checks agree
  with that direction (Strong = 5/5, Moderate = 4/5, Weak = 3 or fewer)
  rather than a numeric percentage.
- Only sets `valid=True` when at least 4 of 5 checks agree AND
  TradingConditions.can_trade is True - a breakout, by definition,
  needs strong alignment, not a bare majority.

TradingConditions is a hard gate on `valid`, not on `direction`: the
technical read is still reported even when trading isn't currently
permitted, so the evaluation stays informative about what the
strategy sees, while `valid=False` makes clear it isn't actionable.
"""

from app.trading.conditions.models import TradingConditions
from app.trading.context.models import MarketContext, TrendContext
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.strategy.models import StrategyDirection, StrategyEvaluation, StrategyStrength

_RSI_BULLISH_THRESHOLD = 55.0
_RSI_BEARISH_THRESHOLD = 45.0

_MIN_AGREEING_CHECKS_FOR_VALID = 4

_Check = tuple[str, StrategyDirection]


def _ema_alignment(snapshot: IndicatorSnapshot) -> _Check:
    if snapshot.close_price > snapshot.ema:
        return "EMA alignment: price above EMA", StrategyDirection.LONG
    if snapshot.close_price < snapshot.ema:
        return "EMA alignment: price below EMA", StrategyDirection.SHORT
    return "EMA alignment: price equal to EMA", StrategyDirection.NONE


def _rsi_confirmation(snapshot: IndicatorSnapshot) -> _Check:
    if snapshot.rsi > _RSI_BULLISH_THRESHOLD:
        return (
            f"RSI confirmation: RSI {snapshot.rsi:.2f} above {_RSI_BULLISH_THRESHOLD:.0f}",
            StrategyDirection.LONG,
        )
    if snapshot.rsi < _RSI_BEARISH_THRESHOLD:
        return (
            f"RSI confirmation: RSI {snapshot.rsi:.2f} below {_RSI_BEARISH_THRESHOLD:.0f}",
            StrategyDirection.SHORT,
        )
    return f"RSI confirmation: RSI {snapshot.rsi:.2f} inconclusive", StrategyDirection.NONE


def _vwap_confirmation(snapshot: IndicatorSnapshot) -> _Check:
    if snapshot.close_price > snapshot.vwap:
        return "VWAP confirmation: price above VWAP", StrategyDirection.LONG
    if snapshot.close_price < snapshot.vwap:
        return "VWAP confirmation: price below VWAP", StrategyDirection.SHORT
    return "VWAP confirmation: price equal to VWAP", StrategyDirection.NONE


def _supertrend_confirmation(snapshot: IndicatorSnapshot) -> _Check:
    if snapshot.supertrend_is_bullish:
        return "SuperTrend confirmation: bullish", StrategyDirection.LONG
    return "SuperTrend confirmation: bearish", StrategyDirection.SHORT


def _trend_agreement(context: MarketContext) -> _Check:
    if context.trend == TrendContext.BULLISH_TREND:
        return "Trend agreement: Market Context trend is bullish", StrategyDirection.LONG
    if context.trend == TrendContext.BEARISH_TREND:
        return "Trend agreement: Market Context trend is bearish", StrategyDirection.SHORT
    return "Trend agreement: Market Context trend is sideways", StrategyDirection.NONE


def _strength_for(agreeing_checks: int) -> StrategyStrength:
    if agreeing_checks >= 5:
        return StrategyStrength.STRONG
    if agreeing_checks == 4:
        return StrategyStrength.MODERATE
    return StrategyStrength.WEAK


class EMABreakoutStrategy:
    name = "EMABreakout"

    def evaluate(
        self,
        snapshot: IndicatorSnapshot,
        context: MarketContext,
        conditions: TradingConditions,
    ) -> StrategyEvaluation:
        checks = (
            _ema_alignment(snapshot),
            _rsi_confirmation(snapshot),
            _vwap_confirmation(snapshot),
            _supertrend_confirmation(snapshot),
            _trend_agreement(context),
        )

        bullish_count = sum(1 for _, direction in checks if direction == StrategyDirection.LONG)
        bearish_count = sum(1 for _, direction in checks if direction == StrategyDirection.SHORT)

        if bullish_count > bearish_count:
            direction = StrategyDirection.LONG
        elif bearish_count > bullish_count:
            direction = StrategyDirection.SHORT
        else:
            direction = StrategyDirection.NONE

        agreeing_checks = max(bullish_count, bearish_count)
        strength = _strength_for(agreeing_checks)

        reasons = [message for message, check_direction in checks if check_direction == direction]
        warnings = [
            message for message, check_direction in checks if check_direction != direction
        ]

        if not conditions.can_trade:
            warnings.append(f"Trading not permitted: {conditions.no_trade_reason}")

        valid = (
            conditions.can_trade
            and direction != StrategyDirection.NONE
            and agreeing_checks >= _MIN_AGREEING_CHECKS_FOR_VALID
        )

        return StrategyEvaluation(
            strategy_name=self.name,
            valid=valid,
            direction=direction,
            strength=strength,
            reasons=reasons,
            warnings=warnings,
        )
