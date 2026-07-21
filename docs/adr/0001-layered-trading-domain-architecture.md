# 0001 - Layered trading domain architecture

## Status

Accepted (established Phase 5, reinforced every phase through Phase 10).

## Context

The pre-rebuild codebase (see `debug/signal-runtime`'s `app/strategy/`
and `app/services/`) mixed indicator calculation, market classification,
signal generation, scoring, and risk sizing into a handful of tightly
coupled modules (`guardian_engine.py`, `rule_engine.py`,
`score_engine.py`, `decision_engine.py`, `risk_engine.py`) that called
each other directly and shared implicit dictionary-shaped data. A bug
in one stage (or a change to its output shape) could silently break
another, and none of it was independently testable without the whole
chain.

## Decision

The trading domain (`app/trading/`) is built as a strict pipeline of
independent packages, each with a single immutable frozen-Pydantic
output model and zero knowledge of the packages downstream of it:

```
indicators/  -> IndicatorSnapshot
context/     -> MarketContext        (consumes IndicatorSnapshot)
conditions/  -> TradingConditions    (consumes MarketContext)
strategy/    -> StrategyEvaluation   (consumes IndicatorSnapshot, MarketContext, TradingConditions)
risk/        -> RiskAssessment       (consumes StrategyEvaluation)
decision/    -> TradeRecommendation  (consumes StrategyEvaluation, RiskAssessment, TradingConditions)
```

Each package's dependency boundary is enforced by convention and
verified with grep at every phase boundary - not just asserted by
design intent - confirming no package imports `app.kite`, `app.api`,
`app.core.database`, `fastapi`, `sqlalchemy`, or `kiteconnect`, and that
cross-package imports go only in the downstream direction shown above.

## Consequences

- Every package is unit-testable in complete isolation, with plain
  constructed inputs - no fakes, no database, no HTTP server needed
  anywhere under `app/trading/`.
- A change to one package's internals cannot silently corrupt another;
  the only contract between packages is the frozen output model.
- Adding a new concern (Trading Conditions in Phase 7, Risk in Phase 9,
  Decision in Phase 10) is a new package plus one new consumer wire-up,
  not a rewrite of existing packages.
- The cost is more files and more explicit plumbing between phases
  than a single monolithic engine would need - accepted deliberately,
  given how much the pre-rebuild monolith's coupling had already cost
  in undiagnosable bugs and leaked credentials.
