# NIFTY Guardian — Walk-Forward Validation Guide

This guide covers `app/validation/` (the Walk-Forward Validation
Framework, Phase 17) - how window types work, how to configure
acceptance criteria, and how to interpret a robustness score. It
assumes familiarity with `docs/OPTIMIZATION_GUIDE.md` (the Grid Search
Engine this package runs on training data only) and
`docs/RESEARCH_GUIDE.md` (the Experiment Framework this package reuses
for both training and testing).

## Purpose

Grid search (Phase 16) answers "which configuration performed best on
this dataset?" - it says nothing about whether that configuration
would have worked on data it never saw. Walk-Forward Validation answers
exactly that question: split history into a sequence of train/test
window pairs, run the Grid Search Engine on **training data only** for
each window, take its best configuration, then run that exact
configuration - unchanged - against **testing data only** (the period
immediately following training, which the optimizer never touched).
Comparing train performance to test performance across many windows is
the entire point: a configuration that performs *close to* its
training result on unseen data generalizes; one whose performance
collapses out-of-sample was overfit to its training window.

**This is not another optimizer.** `app/validation/` calculates
nothing itself beyond the pass/fail comparisons in `validator.py` - it
orchestrates the existing (frozen) Grid Search Optimization Engine
(Phase 16) and Experiment/Backtest/Analytics Frameworks (Phases 11, 12,
14), deciding only what data each one sees and comparing their outputs.

## Rolling vs. Expanding vs. Anchored

All three window types are deterministic - the same `WindowConfig` and
dataset always produce the same windows in the same order, and window
generation stops the moment a window's test period would run past the
available data (no partial final window is ever produced).

- **Rolling**: both the training window and the testing window slide
  forward together by `step_size_days` each iteration; training
  duration stays constant. Example (`training_duration_days=365*2`,
  `testing_duration_days=365`, `step_size_days=365`): Train 2021-2022 →
  Test 2023, then Train 2022-2023 → Test 2024. Answers "does this
  configuration keep working if I always retrain on the most recent N
  years?"
- **Expanding**: the training window's start is fixed at the dataset's
  own beginning; its end grows by `step_size_days` each iteration, so
  training duration increases every window. Example: Train 2021 → Test
  2022, then Train 2021-2022 → Test 2023, then Train 2021-2023 → Test
  2024. Answers "does more training history make the configuration
  more reliable, or does old data eventually stop helping?"
- **Anchored**: the training window is fixed after the very first
  window (trained once, on the earliest data) and never changes; only
  the testing window slides forward. Answers "does a configuration
  chosen once, early on, keep working as time passes?" - the strictest
  test of the three, since it never lets the strategy adapt to newer
  data at all.

Pick Rolling when you expect the market's behavior to genuinely change
over time and want to periodically retrain closer to "now." Pick
Expanding when you believe more history is strictly better (or want to
find out). Pick Anchored when you want to know how long a single,
never-updated configuration survives.

## Why Walk-Forward matters

A grid search winner is, by construction, whichever configuration
happened to fit its training data best - `docs/OPTIMIZATION_GUIDE.md`'s
"Avoiding overfitting" section already warns that this is not the same
as being good in general. Walk-forward validation is the concrete
mechanism for actually checking that claim, rather than just warning
about it: it repeats the "pick a winner, then see how it does on data
it hasn't seen" cycle many times across history, so one lucky test
period can't carry the whole conclusion.

## Avoiding overfitting

Everything in `docs/RESEARCH_GUIDE.md` and `docs/OPTIMIZATION_GUIDE.md`
applies with extra force here:

- **A high robustness score from few windows is weak evidence.** Three
  windows that all happened to pass tells you much less than twenty
  that mostly did - widen the dataset or shrink the step size before
  trusting a small window count's score.
- **Watch `min_trade_count` failures as closely as outright losses.** A
  test window with only 1-2 trades passing every other rule is not
  "robust" - it's a coin flip that happened to land right, exactly the
  sample-size trap `docs/RESEARCH_GUIDE.md` already describes for a
  single backtest.
- **Parameter instability is itself a warning sign.** If
  `ParameterStability.distinct_value_count` is high (the optimizer
  picks a different "best" configuration almost every window), the
  parameter space is likely too sensitive to short-term noise in the
  training data to trust any single window's winner.
- **A validation run is still only as good as its dataset.** Walk-
  forward across many windows of the *same* narrow historical period
  (e.g., only one bull market) tells you nothing about a different
  regime - it reduces overfitting to one window, not overfitting to
  one *kind* of market.

## Acceptance criteria / Failure criteria

`ValidationRules` has **no default values** - every threshold must be
supplied explicitly (the CTO brief's "Do NOT hardcode thresholds"),
enforced by the model itself: constructing `ValidationRules()` with no
arguments raises immediately. Four per-window rules plus one run-level
rule:

| Rule | Field | Meaning |
|---|---|---|
| Maximum Drawdown increase | `max_drawdown_increase_percent` | test `max_drawdown` may be at most this many percent worse than train's. Train drawdown of exactly zero is a special case: any nonzero test drawdown fails (there is no meaningful percentage over a zero base). |
| Minimum Profit Factor | `min_profit_factor` | test profit factor must be at least this. An **undefined** test profit factor (no losing trades to divide by, or zero trades) is treated as a **fail**, not a pass - a conservative default, since the rule cannot actually be verified. |
| Maximum performance degradation | `max_performance_degradation_percent` | test net profit may be at most this many percent worse than train's. Train net profit of exactly zero is a special case: any negative test result fails. |
| Minimum trade count | `min_trade_count` | test `total_trades` must be at least this - guards against trusting a result built on too few trades. |
| Minimum robustness score | `min_robustness_score_percent` | the run-level pass/fail: at least this percent of *completed* windows must individually pass every rule above. |

`WindowConfig.minimum_candles`/`minimum_trades` are a separate, earlier
gate - they decide whether a window is even attempted (data
sufficiency), not whether its outcome passes. A window whose train or
test slice has fewer than `minimum_candles` is marked
`INSUFFICIENT_DATA` before any optimization runs; a window whose best
*training* configuration made fewer than `minimum_trades` is also
marked `INSUFFICIENT_DATA` (its "best" pick isn't trustworthy enough to
test) rather than proceeding to a test run built on a shaky foundation.

## Recommended defaults

These are suggestions to start from, not hardcoded anywhere in the
framework - choose values that match your own risk tolerance and
dataset size:

- `max_drawdown_increase_percent`: **50.0** - test drawdown up to 50%
  worse than train is a soft warning sign, not disqualifying on its
  own; much higher suggests genuine overfitting to train's specific
  drawdown episodes.
- `min_profit_factor`: **1.2** - comfortably above break-even (1.0),
  leaving room for the deterioration validation itself is designed to
  detect.
- `max_performance_degradation_percent`: **30.0** - some degradation
  from train to test is normal and expected; 30% is a starting point
  for "meaningfully worse," not "identical."
- `min_trade_count`: **20** - the same rule-of-thumb floor
  `docs/RESEARCH_GUIDE.md` already recommends for trusting a ratio
  computed from a trade sample.
- `min_robustness_score_percent`: **60.0** - a configuration that only
  held up in a bare majority of windows is not yet "robust"; 60% is a
  deliberately modest bar above chance, not a high one.

## Interpreting robustness

`ValidationReport.robustness_score` is **deliberately simple**: the
percentage of *completed* windows (excluding `INSUFFICIENT_DATA` and
`FAILED` ones - averaging in a window that never produced a result
would be meaningless, not conservative) that passed every configured
rule. It is not a continuous, degradation-weighted score - a window
that missed one rule by a hair counts exactly the same as one that
missed every rule badly. This is an intentional simplicity trade-off:
a transparent, easily-audited score over an opaque formula that
weights failures in ways a reader would have to reverse-engineer. A
more nuanced continuous score is a reasonable future extension, not
implemented here.

Read the robustness score alongside, never instead of:

- **`completed_windows` vs. `total_windows`** - a high score computed
  from 2 completed windows out of 10 attempted is not the same claim
  as 9 out of 10.
- **`average_performance_degradation_percent`** - the *magnitude* of
  degradation across windows, which the pass/fail score alone doesn't
  convey (a 65% robustness score with 5% average degradation reads very
  differently from the same score with 45% average degradation).
- **Parameter stability** - see "Avoiding overfitting" above.
- **The window-by-window summary** - whether failures cluster in one
  stretch of history (a regime change) or scatter randomly (generic
  overfitting) changes what you should do about it.

## Demo

`scripts/demo_walk_forward.py` generates a small synthetic dataset,
runs Rolling-window validation with a deliberately small search space,
prints every window's train/test comparison, and reports the overall
robustness score:

```bash
python3 scripts/demo_walk_forward.py
```
