# 0005 - Risk evaluated independently of strategy validity

## Status

Accepted (Phase 9, consumed by Phase 10).

## Context

The pre-rebuild `debug/signal-runtime` branch's `risk_engine.py` took a
`confidence` percentage and a `signal` string together and derived
stop-loss/target points from *how confident* the system already was in
the trade - risk sizing and trade validity were the same calculation,
so a technically strong signal always got a wider stop and bigger
targets, whether or not that was actually a sound risk trade-off.

## Decision

`app/trading/risk/` evaluates position sizing, stop-loss, target,
reward/risk, and four risk-limit gates (daily loss, max trades per day,
capital exposure, max concurrent positions) from `StrategyEvaluation`,
`RiskConfig`, and `CapitalState` alone. `RiskAssessment.risk_ok`
reflects only the four risk-limit gates plus a minimum-viable-position
check - it never reads `StrategyEvaluation.valid`, and a strategy's
`strength` does not change how stop-loss/target are sized (ATR-based,
not confidence-tiered). `StrategyEvaluation` is consulted for exactly
one thing: `direction`, to place stop-loss/target on the correct side
of `entry_price`.

The Decision Engine (Phase 10) is the first and only layer allowed to
combine `StrategyEvaluation.valid` and `RiskAssessment.risk_ok`
together - each of Phases 8 and 9 independently gates on its own
concern, and Phase 10 is where both gates, plus `TradingConditions`,
finally meet.

## Consequences

- A change to strategy scoring logic can never silently change how
  much capital a trade risks, and vice versa - the two calculations
  cannot leak into each other.
- `RiskAssessment` is meaningful and testable on its own, independent
  of whether the strategy that produced its `direction` was ultimately
  valid - useful for "what would this cost me" questions even for a
  rejected setup.
- This does mean a technically weak signal and a technically strong
  signal with identical direction get identically-sized stops/targets;
  if strength should ever influence sizing, that is a deliberate,
  separately-reviewed change to `risk/`, not an implicit side effect of
  `strategy/`.
