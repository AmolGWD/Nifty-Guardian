# NIFTY Guardian — Optimization Guide

This guide covers `app/optimization/` (the Grid Search Strategy
Optimization Engine, Phase 16) - how to define a search space, run an
exhaustive grid search, interpret and compare the results, and avoid
the most common mistakes. It assumes familiarity with
`docs/RESEARCH_GUIDE.md` (the Strategy Experiment Framework this
package orchestrates) and `docs/PARAMETER_CATALOG.md` (the Parameter
Injection Framework this package sweeps).

## Purpose

Grid search answers one narrow question: "of these specific
configurations, which performed best on this dataset, by this
metric?" It does not answer "what is the best possible configuration"
(it only ever sees the combinations you defined), and it does not
answer "will this configuration keep working" (that needs Walk-Forward
Validation, a later phase). This package introduces no AI, no strategy
logic changes, and no randomization - `app/optimization/executor.py`
constructs a `StrategyParameters`/`RiskConfig` pair for every point in
a Cartesian product of parameter ranges, runs each one through the
existing (frozen) `app.research`/`app.trading.backtest`/
`app.trading.analytics` pipeline exactly as a single manually-run
experiment would, and ranks the results.

## Grid Search philosophy

- **Exhaustive, not smart.** Every combination in the search space is
  actually run - there is no early stopping, no gradient, no
  Bayesian search. This is deliberate: exhaustive search is completely
  transparent (you can always answer "why wasn't X tried" - it either
  is or isn't in the grid) at the cost of scaling combinatorially with
  the number of parameters and their step counts. Keep search spaces
  small (the CTO brief's own demo example is 3×2×2 = 12 combinations)
  until you have a specific reason to widen one dimension.
- **Deterministic, not random.** `grid_generator.generate_grid()` is a
  fixed Cartesian product in a fixed order - the same `ParameterSpace`
  always produces the same combinations in the same order, and running
  the same search space against the same dataset twice produces
  identical results (see
  `tests/optimization/test_executor.py::test_run_grid_search_no_randomization_same_inputs_same_outputs`).
  There is nothing to seed and nothing that varies run to run.
- **One combination, one Experiment.** Every combination becomes its
  own `Experiment` (via `app.research.experiment.create_experiment()`)
  with the grid values recorded in both `Experiment.parameters` (so
  they show up in every export automatically) and
  `OptimizationResult.parameter_values` - reusing Phase 14's framework
  completely rather than reimplementing backtest orchestration.

## Which parameters can actually change a result this phase

Of the CTO brief's six named parameters, **all six now genuinely
change a real backtest outcome** - but this required a narrow,
explicitly CTO-authorized exception to `app.trading.backtest`'s
freeze, decided during this phase's planning rather than assumed:

| Parameter | Applied as | Genuinely wired? |
|---|---|---|
| `reward_risk_ratio` | `RiskConfig.target_atr_multiplier = reward_risk_ratio * stop_loss_atr_multiplier` (holding the base config's `stop_loss_atr_multiplier` fixed) | Yes - always was, via `BacktestConfig.risk_config` |
| `risk_percent` | `RiskConfig.risk_per_trade_percent` | Yes - always was |
| `max_trades_per_day` | `RiskConfig.max_trades_per_day` | Yes - always was |
| `rsi_bullish_threshold` | `StrategyParameters.rsi_bullish_threshold` | Yes - **only since this phase** |
| `rsi_bearish_threshold` | `StrategyParameters.rsi_bearish_threshold` | Yes - **only since this phase** |
| `ema_period` | `BacktestConfig.ema_period` -> `calculate_indicator_snapshot(ema_period=...)` | Yes - **only since this phase** |

Before this phase, `app.trading.backtest.backtest_engine.run_backtest()`
always built `StrategyRegistry`/`EMABreakoutStrategy()` via the
parameterless `default_registry()`, with no way to inject a
`StrategyParameters` into an actual backtest run - not even
`EMABreakoutStrategy`'s own Phase 15 injection point could reach a real
result through the Backtest Engine, and `ema_period` was never passed
to the indicator engine at all. Phase 16's planning surfaced this gap
before any code was written (it would otherwise have meant every grid
combination varying EMA/RSI produced byte-identical results, easily
misread as "these parameters don't matter" rather than "this phase
can't wire them yet" - the same honest-placeholder problem
`docs/PARAMETER_CATALOG.md` and `docs/RESEARCH_GUIDE.md` had already
flagged for exactly these parameters). The CTO explicitly chose to
authorize a minimal, additive fix rather than accept a degraded search
space: `BacktestConfig` gained two new optional fields -
`strategy_parameters: StrategyParameters | None = None` and
`ema_period: int = 20` - both defaulting to the exact prior hardcoded
behavior, so every pre-existing `BacktestConfig(...)` call site and
every previously-passing test is unaffected. See
`app/trading/backtest/models.py`'s and `backtest_engine.py`'s
docstrings for the exact diff.

## Parameter selection

- **Only optimize what genuinely represents a trade-off, not a safety
  limit.** `parameter_space.py`'s `safe_to_optimize` field on every
  `OptimizableParameter` should mean "letting a search choose this
  value can't defeat the point of having it" - `max_daily_loss`,
  `max_concurrent_positions`, and `max_capital_exposure_percent` are
  deliberately absent from `DEFAULT_PARAMETER_CATALOG` for exactly this
  reason (see `docs/PARAMETER_CATALOG.md`'s risk table), even though
  they're `RiskConfig` fields.
- **The CTO brief's "Do NOT optimize" list is enforced, not just
  documented.** `ParameterSpace`/`OptimizableParameter` raise
  `ParameterValidationError` if asked to include VWAP toggle,
  SuperTrend toggle, any session filter, or the expiry filter - these
  change *what the strategy is*, not *how well-tuned it is*, and don't
  fit this model's minimum/maximum/step shape anyway (they're
  booleans/session windows, not swept numeric ranges).
- **Widen a search space one dimension at a time.** Going from a 3×2
  grid to a 3×2×3 grid multiplies the number of experiments run by 3 -
  know what that will cost in wall-clock time before doing it (see
  `progress.py`'s estimated-remaining-time below).

## Avoiding overfitting

Everything in `docs/RESEARCH_GUIDE.md`'s "Avoiding overfitting" section
applies here with extra force, because grid search runs *many*
configurations against the *same* dataset and then picks a "winner" -
that winner is, by construction, whichever configuration happened to
fit this specific data best, which is not the same as being the best
configuration in general:

- **Never trust a single grid search run on a single dataset as a
  final answer.** Re-run the winning configuration (or the top few)
  against a different date range before acting on it.
- **Watch total trade counts, not just the ranking.** A configuration
  that "wins" on 2-3 total trades tells you about sample-size noise,
  not strategy quality - the same rule from `docs/RESEARCH_GUIDE.md`
  applies per-combination here.
- **A parameter that "improves" the weighted score at every single grid
  value is suspicious**, not reassuring - it usually means the dataset
  is too small/uniform to reveal any real trade-off (see this guide's
  own worked example below: on the small 75-candle sample dataset, EMA
  period genuinely has no effect on trades taken at all, purely
  because the sample is one continuous, strongly-trending series - not
  because EMA period doesn't matter in general).
- **The more parameters you sweep at once, the more likely you are to
  find a combination that looks great by chance alone** ("garden of
  forking paths") - prefer several small, targeted searches (one or
  two parameters each) with a stated hypothesis, over one enormous
  search across all six parameters at once.

## Metric interpretation

`RankBy` (`app/optimization/ranking.py`) supports the CTO brief's seven
ranking modes. Six of them (`ProfitFactor`, `NetProfit`, `SharpeRatio`,
`RecoveryFactor`, `MaxDrawdown`, `WinRate`) delegate entirely to
`app.research.ranking.rank_experiments()`/`extract_metric()` - see
`docs/RESEARCH_GUIDE.md`'s "Meaning of each primary metric" for what
each one means; nothing about their interpretation changes here.

`RankBy.WeightedScore` (the default) delegates to
`app.research.scoring.calculate_scores()` with
`DEFAULT_SCORING_WEIGHTS` - Profit Factor and Sharpe Ratio weighted
0.3 each, Recovery Factor and Win Rate weighted 0.2 each. This is **a
reasonable default, not the only valid choice**: it favors
consistency (Sharpe) and being net-profitable-per-unit-of-loss (Profit
Factor) over raw Net Profit or Max Drawdown alone, on the reasoning
that a configuration that's merely "profitable and survivable" is a
better search-space winner than one that's "extremely profitable but
fragile." Pass your own `ScoringWeights` to `optimize()`/
`rank_optimization_results()` if a different balance suits your
question better - scores are only comparable *within* one ranked batch
(same caveat as `app.research.scoring`'s own docstring).

## How to compare optimization runs

- **Compare `OptimizationReport`s side by side**, not raw exports -
  `report.py`'s per-parameter summary (average weighted score per
  distinct value tested) is usually more informative than eyeballing
  every combination's row, since it directly answers "does raising
  this one parameter tend to help."
- **A parameter summary entry's `average_weighted_score` is an average
  across every *other* combination varied alongside it** - if your
  search space has several dimensions, a single parameter's summary
  entry mixes together its performance across all the other
  parameters' values too. Keep search spaces small and focused (see
  "Parameter selection") so this stays interpretable.
- **Record `OptimizationRun.run_id` and each combination's
  `Experiment.git_commit_hash`** (recorded automatically by
  `create_experiment()`) the same way `docs/RESEARCH_GUIDE.md`
  recommends for a single experiment - a grid search result you can't
  reproduce against the same commit and dataset isn't a comparison
  point.

## Common mistakes

- **Treating the top-ranked configuration as "the answer."** It is the
  best of the combinations you tried, on the data you tried them on -
  see "Avoiding overfitting" above.
- **Sweeping `ema_period`/RSI thresholds and a risk parameter together,
  then attributing the result to the strategy parameter alone.** Since
  Phase 16 wires all six parameters simultaneously, a search result
  that looks great could be driven entirely by the risk-side
  parameters (which affect position sizing/targets directly) rather
  than the strategy-side ones (which affect trade *selection*) -
  `report.py`'s per-parameter summary exists to help you tell these
  apart, but only if you read it.
- **Forgetting `ema_period` has a hard floor.** `run_backtest()` raises
  if `ema_period` exceeds the candles available in the warmup window -
  a search space with a wide `ema_period` range on a small dataset will
  produce `FAILED` results at the high end, not silently-wrong ones
  (see `docs/RESEARCH_GUIDE.md`'s own "When to reject an experiment").
- **Assuming every metric's distribution has values.** A metric like
  Sharpe Ratio can be `None` for every completed combination on a
  small/short dataset (too few daily equity points) -
  `report.py`'s `MetricDistribution.sample_size == 0` is Analytics
  being honest about that, not a bug.

## Future extensions

This phase is explicitly grid search only - the CTO brief's next phase
is Walk-Forward Validation (testing whether a winning configuration
holds up out-of-sample, on data the search never saw), not smarter
search. Candidates for later, separately-reviewed phases: random/
Bayesian search (for search spaces too large to run exhaustively),
walk-forward-aware ranking (penalizing configurations that only win on
one time window), and exposing `SessionParameters` for optimization
once `app.trading.conditions` has its own equivalent injection seam.
