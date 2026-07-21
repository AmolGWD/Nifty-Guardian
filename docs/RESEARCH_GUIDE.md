# NIFTY Guardian — Research Guide

This guide covers `app/research/` (the Strategy Experiment Framework,
Phase 14) - how to design, run, compare, and judge experiments against
the existing (frozen) Backtest and Analytics Engines. It assumes
familiarity with `docs/SYSTEM_ARCHITECTURE.md`.

## Purpose of experiments

An experiment is one reproducible run of one strategy, against one
dataset, with one configuration - packaged together with its outcome
so it can be compared against other runs later. The Experiment
Framework does not optimize strategies and does not change trading
logic; it exists so that research is *repeatable* and *comparable*:
the same experiment run twice (same dataset, same config, same code
version) should produce the same result, and two different experiments
should be comparable on the same terms.

Concretely, an `Experiment` (`app/research/models.py`) records what was
run - name, description, strategy, dataset path, timeframe,
`BacktestConfig` (the real, tunable configuration), a free-form
`parameters` dict (research metadata - see "Parameter management"
below), tags, notes, and (best-effort) the git commit hash of the code
that ran it. Running it (`app/research/experiment_runner.py`) produces
an `ExperimentResult` - the `Experiment` plus its `BacktestResult`,
`AnalyticsReport`, status, and duration.

## Research workflow

1. **Form a hypothesis.** "Does raising `stop_loss_atr_multiplier`
   from 1.5 to 2.0 reduce how often stops get hit, at the cost of a
   deeper max drawdown?" - something specific enough that a single
   comparison can answer it.
2. **Create the experiment(s).** Use `experiment.create_experiment()`
   to build one `Experiment` per configuration you're testing. Vary
   exactly one thing between them where possible (see "Parameter
   management").
3. **Run them.** `experiment_runner.run_experiment()` (one) or
   `run_experiments()` (many) - each invokes the existing Backtest
   Engine then Analytics Engine and returns an `ExperimentResult`,
   catching any failure (bad dataset path, too few candles, ...) as a
   `FAILED` result rather than crashing the batch.
4. **Register them.** `ExperimentRegistry.register()`/`record_result()`
   so they're retrievable by id or tag later - this is in-memory only
   this phase (no database), same as `app.data`'s repository.
5. **Compare and rank.** `comparison.compare_experiments()` for a
   side-by-side metric table; `ranking.rank_experiments()` to sort by
   one metric; `scoring.calculate_scores()` for a single weighted
   score across several metrics at once.
6. **Export and record the conclusion.** `export.export_markdown()`/
   `export_csv()`/`export_json()`, plus your own written conclusion
   (in the experiment's `notes`, or in a separate research log) - a
   comparison table without a stated conclusion is not a finished
   experiment.

## Naming conventions

- **Experiment name**: short, human-readable, and specific to what
  changed - `"Balanced"`, `"Conservative"`, `"Stop 2xATR"` - not
  `"Test 1"`. If you're running a sweep, include the varying value in
  the name (`"RiskPercent-0.5"`, `"RiskPercent-1.0"`).
- **Tags**: use tags for things you'll want to filter by later, not
  for what varied this run - `"baseline"`, `"regression-check"`,
  `"pre-optimization"`. Keep the tag vocabulary small and reused, not
  one-off per experiment.
- **Description**: one sentence, what's being tested, not what the
  strategy does (the strategy's own behavior is documented in
  `docs/SYSTEM_ARCHITECTURE.md`, not repeated per experiment).

## Parameter management

`Experiment.parameters` is a free-form `dict[str, str | int | float |
bool]` - the framework stores and exports it, and never interprets it.
This is deliberate: today, the only things actually wired into a real
backtest run are `Experiment.backtest_config` and its nested
`risk_config` - real Pydantic fields with real effects
(`risk_per_trade_percent`, `stop_loss_atr_multiplier`,
`target_atr_multiplier`, `max_daily_loss`, `max_trades_per_day`,
`max_concurrent_positions`, `max_capital_exposure_percent`,
`warmup_candles`, session/window settings, ...). The frozen
`EMABreakoutStrategy` has no external parameterization hook at all -
its RSI thresholds are module-level constants - so a `parameters` entry
like `"rsi_threshold": 60` records your *intent*, not something the
strategy actually reads. Wiring arbitrary strategy parameters through
is Strategy Optimization's job (the next phase), not this one.

Two practical rules follow from that:

- **Always mirror what you vary in `backtest_config` into
  `parameters` too**, even though it's redundant - `parameters` is
  what shows up in every export, and `backtest_config` is a large
  nested object that isn't as scannable in a comparison table.
- **Don't invent a `parameters` entry for something you haven't
  actually made real** - if you write `"ema_period": 9` today, it does
  nothing; label it clearly as aspirational (e.g. a note, not a bare
  parameter) until Strategy Optimization gives it a real effect, or a
  future reader will reasonably assume it did something.

## How to compare experiments

`comparison.compare_experiments(results, metrics)` returns one row per
experiment with exactly the metrics you asked for (`Metric` in
`app/research/models.py`: `NET_PROFIT`, `PROFIT_FACTOR`, `EXPECTANCY`,
`MAX_DRAWDOWN`, `RECOVERY_FACTOR`, `SHARPE_RATIO`, `CALMAR_RATIO`,
`WIN_RATE`). Always compare on **more than one metric** - a higher net
profit with a much deeper drawdown is not unambiguously "better," it's
a different risk/reward trade-off. Prefer:

- **`ranking.rank_experiments(results, metric)`** when you have one
  metric you've decided matters most for this decision (e.g., "which
  of these three configs has the best Sharpe Ratio") - missing values
  (a `FAILED` result, or a metric Analytics couldn't compute) always
  sort last, regardless of the metric's direction.
- **`scoring.calculate_scores(results, weights)`** when several
  metrics matter together (see "Meaning of each primary metric" for
  what a sensible weight split looks like). Scores are computed by
  min-max normalizing each metric *across the batch you passed in* -
  they are only meaningful relative to each other within that same
  call, never as an absolute score you can compare across separate
  scoring runs with different experiment sets.

## Avoiding overfitting

The single biggest risk in this kind of research is tuning a
configuration until it looks great on one specific dataset, which
tells you nothing about how it will behave on data it hasn't seen.
Concretely:

- **Never judge a configuration from one backtest run on one dataset.**
  If you only have the one sample dataset available, treat any
  conclusion from it as provisional, not a result.
- **Watch for a suspiciously small number of trades.** A backtest with
  2-3 trades can show an extreme Sharpe Ratio or CAGR purely from
  sample-size noise (see "Meaning of each primary metric" below,
  Sharpe/CAGR) - neither should be trusted with fewer trades/days than
  needed to make the ratio's underlying assumptions reasonable.
- **Be suspicious of a parameter change that "improves" every single
  metric at once.** Real trade-offs usually show up somewhere (a
  slightly lower win rate for a much better profit factor, say); if
  nothing got worse, check whether the dataset is simply too small or
  too specific to reveal the trade-off.
- **Re-run the same configuration on a different date range before
  trusting it.** A configuration that only works in one particular
  historical stretch (one trend regime, one volatility regime - see
  Analytics' Market Regime Analysis, Phase 12) is overfit to that
  stretch, not validated.

## When to reject an experiment

Reject (don't act on) an experiment's result when:

- **`status` is `FAILED`.** Check `error` - a bad dataset path or too
  few candles for the warmup window are the common causes, not a
  finding about the strategy.
- **Total trades is too small to trust any ratio computed from it**
  (rule of thumb: fewer than ~20-30 trades for Sharpe/Sortino/Calmar to
  mean much, fewer still for CAGR/Annual Return over a short date
  range - see below).
- **The result depends on a `parameters` entry that isn't actually
  wired into anything** (see "Parameter management") - you haven't
  tested what you think you tested.
- **You can't reproduce it.** `Experiment.git_commit_hash` exists for
  exactly this reason - if a result can't be reproduced against the
  same commit and the same dataset, don't trust it as a comparison
  point going forward.

## Meaning of each primary metric

- **Net Profit** - final capital minus initial capital, absolute
  currency. Says nothing about how much capital or time it took to
  get there - always read alongside Max Drawdown.
- **Profit Factor** - gross profit / gross loss. Above 1 means net
  profitable; below 1 means net losing, regardless of win rate. `None`
  when there are no losing trades to divide by.
- **Expectancy** - average profit per trade (net profit / total
  trades). The number that answers "if I took one more trade like
  these, what would I expect to make."
- **Win Rate** - percentage of trades that closed profitably. A high
  win rate with a low profit factor usually means many small wins and
  a few large losses (or the reverse) - never read in isolation.
- **Maximum Drawdown** - the single deepest peak-to-trough decline in
  equity, absolute currency. The metric most directly about "how bad
  could it get" - the one metric in this framework where **lower is
  better** (`Metric.MAX_DRAWDOWN` is the one entry in
  `models.LOWER_IS_BETTER`).
- **Recovery Factor** - net profit / max drawdown. How much profit was
  generated per unit of the worst pain endured; `None` when there was
  no drawdown to divide by.
- **Sharpe Ratio** - annualized mean daily return divided by its
  standard deviation. Rewards consistency, penalizes volatility in
  either direction (a few huge wins hurt Sharpe just as volatility
  does). `None` with fewer than 3 daily equity points or zero return
  variance (Analytics, Phase 12) - a missing Sharpe Ratio is Analytics
  being honest that there isn't enough data, not a zero.
- **Calmar Ratio** - CAGR divided by max drawdown percentage. Answers
  "how much annualized growth per unit of worst-case pain," `None`
  without a valid CAGR or with zero drawdown.

## Best practices

- **Vary one thing at a time** where the question calls for it - a
  three-way comparison that changes two parameters between every run
  can't tell you which change caused what.
- **Always export.** A comparison printed to a terminal and never
  saved is not reproducible research - `export_markdown()` for a
  human-readable record, `export_json()`/`export_csv()` for anything
  you'll want to load and re-analyze later.
- **Record the git commit hash and treat it as load-bearing.** If
  you're comparing an experiment run today against one from last week,
  check whether the frozen packages changed in between - the CTO
  review process in this project's history means they mostly don't,
  but "mostly" is not "never."
- **Write the conclusion down, not just the numbers.** A future reader
  (including future you) benefits far more from "rejected: only 2
  trades, not enough data" than from a comparison table with no
  interpretation attached.
