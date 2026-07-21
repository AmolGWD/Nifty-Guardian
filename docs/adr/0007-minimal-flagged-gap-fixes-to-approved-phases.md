# 0007 - Minimal, flagged gap-fixes to already-approved phases

## Status

Accepted (recurring policy since Phase 4).

## Context

A strictly layered architecture (ADR-0001) means a later phase
sometimes discovers that an earlier, already-reviewed-and-approved
phase is missing a field or behavior the new phase genuinely needs -
for example:

- Phase 4 found `main.py` never called `Base.metadata.create_all()`,
  so every Kite-authenticated route 500'd instead of cleanly 401'ing.
- Phase 6 found `IndicatorSnapshot` had no volatility measure, so it
  added `atr`/`atr_percent` as a ninth indicator.
- Phase 8 found `IndicatorSnapshot` had no price field, so the EMA
  Breakout Strategy's "price above/below EMA/VWAP" checks had nothing
  to compare against; it added `close_price`.
- Phase 9 found none of its four stated inputs (`StrategyEvaluation`,
  `TradingConditions`, Configuration, Capital settings) carried a price
  or a volatility measure, so it added `entry_price` and `atr` as
  explicit parameters.

## Decision

When a phase finds a genuine gap in earlier, approved work: make the
smallest change that closes the gap (typically one additive field or
parameter, never a redesign), and flag it prominently and explicitly -
in code comments, in the phase's README section, and in the phase
summary - rather than silently expanding scope or working around it
with a duplicate/parallel field. Each fix is reviewed and approved
alongside the phase that needed it, not assumed.

Symmetrically, when a phase's stated inputs would force in a parameter
with no genuine use (Phase 9's `TradingConditions`, listed in that
phase's brief but not needed by any of its eight risk evaluators), the
decision is to leave it out and flag *that* explicitly too, rather than
carry dead parameters for literal interface compliance.

## Consequences

- Earlier phases stay minimal and correct rather than accumulating
  speculative fields "just in case" - additions happen exactly when a
  concrete downstream need proves they're required.
- Every such change is traceable: each gap-fix names which phase found
  it, why, and what the smallest closing change was, both in the
  relevant docstring and in that phase's summary.
- The trade-off is that a phase's interface is not perfectly fixed at
  review time - Phase 9's `RiskConfig`/`CapitalState` inputs, for
  example, were not anticipated until Phase 9 itself. This is treated
  as expected cost of building layer-by-layer rather than designing the
  whole domain up front, not as scope creep.
