# 0006 - Immutable, frozen domain models everywhere

## Status

Accepted (established Phase 2, held through Phase 10).

## Context

The pre-rebuild codebase passed plain `dict` objects between stages
(`market`, `indicators`, `rules`, `decision` in
`debug/signal-runtime`'s `guardian_engine.py`), with no fixed shape,
no type checking, and any stage free to mutate a shared dict in place.
Tracing what a given field meant, or where it was last written, meant
reading every function in the chain.

## Decision

Every domain output in this rebuild is a Pydantic `BaseModel` with
`model_config = ConfigDict(frozen=True)`: `IndicatorSnapshot`,
`MarketContext`, `TradingConditions`, `StrategyEvaluation`,
`RiskAssessment`, `RiskConfig`, `CapitalState`, `TradeRecommendation`,
and every intermediate result type (`SuperTrendResult`,
`StrategyCandidate`, ...). Fields are explicitly typed, required unless
a default is genuinely sensible, and attempting to mutate an instance
after construction raises `pydantic.ValidationError` - verified by a
dedicated immutability test in every phase.

## Consequences

- A function's output type is a complete, self-documenting contract -
  no need to trace call sites to know what fields exist or what they
  mean.
- Once constructed, a result can be passed to multiple downstream
  consumers (as `StrategyEvaluation` is, into both `risk/` and
  `decision/`) with no risk one of them mutates it out from under
  another.
- The cost is verbosity - every new field means updating a model
  definition, not just adding a dict key - accepted deliberately in
  exchange for the type-checking and immutability guarantees `mypy
  --strict` and pydantic provide.
