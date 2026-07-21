# 0004 - Plugin architecture for strategies

## Status

Accepted (Phase 8).

## Context

The pre-rebuild `debug/signal-runtime` branch had exactly one hardcoded
rule set (`rule_engine.py`'s dictionary of named rules), directly
referenced by `guardian_engine.py`. Adding a second strategy would have
meant branching inside that one engine, growing an already-tangled
scoring/decision flow (see ADR-0002) rather than adding an independent
unit.

## Decision

`app/trading/strategy/` defines a `Strategy` Protocol (a `name`
attribute plus `evaluate(snapshot, context, conditions) ->
StrategyEvaluation`), a `StrategyRegistry` that strategies register
with, and `run_strategies()`, which executes every registered strategy
against the same three inputs and returns their evaluations - it does
not compare, rank, or choose between them (Phase 10's Decision Engine
does that). One concrete strategy, `EMABreakoutStrategy`, is
implemented and registered by `default_registry()`.

## Consequences

- A second strategy is a new file implementing `Strategy` plus one line
  registering it - no change to `engine.py`, `registry.py`, or any
  existing strategy.
- Every strategy is independently unit-testable against the same three
  frozen input types, with no dependency on any other strategy.
- The registry currently has no persistence or dynamic loading (it is
  populated in-process by `default_registry()`); if strategies ever
  need to be enabled/disabled at runtime without a code change, that is
  new, explicitly-scoped work, not assumed here.
