# NIFTY Guardian — Monte Carlo Analysis Guide

This guide covers `app/monte_carlo/` (the Monte Carlo Analysis
Framework, Phase 18) - how simulations perturb a backtest's trades,
what each perturbation models, and how to read the resulting
statistics. It assumes familiarity with `docs/OPTIMIZATION_GUIDE.md`
and `docs/VALIDATION_GUIDE.md` (the two prior robustness-checking
phases this one complements, not replaces).

## Purpose

A single backtest produces one trade sequence, one equity curve, one
final number. Monte Carlo analysis asks a different question: **if the
same strategy, on the same historical data, had experienced slightly
different execution conditions - a different fill price, a missed
order, trades landing in a different sequence - how differently could
the outcome have turned out?** It perturbs an already-completed
backtest's `BacktestTrade` list many times (each perturbation modeling
one specific source of real-world execution uncertainty) and measures
the resulting distribution of outcomes, rather than trusting the one
outcome that happened to occur.

**This is not another optimizer and does not change trading logic.**
`app/monte_carlo/` never re-runs the strategy, re-evaluates an
indicator, or re-decides a trade - it only perturbs the *outcomes* of
trades that already happened (via `app/monte_carlo/perturbations/`)
and recomputes what the resulting equity curve and drawdown would have
been, reusing `app.trading.backtest.performance.calculate_max_drawdown`
directly for that one piece of arithmetic rather than duplicating it.

## Simulation philosophy

Each of the six perturbations models one independent, real source of
execution uncertainty, and each is applied through its own `apply(...)`
function that knows nothing about any other perturbation - a
`PerturbationConfig` selects any combination of them, and
`simulation.py` chains whichever are enabled in one fixed, documented
order (trade shuffle → slippage → commission → execution delay →
missed trades → position variation) so the same seed always reproduces
the exact same sequence of simulated outcomes.

- **Trade Order Shuffle** tests whether the same set of trades, in a
  different sequence, could have produced a worse drawdown path - the
  final total is unaffected (it's the same trades), but the *path* to
  get there is not.
- **Slippage** worsens every entry/exit fill by a configurable
  percentage (0.05%/0.10%/0.25% are reasonable starting points) - a
  Long entry fills higher than quoted, a Long exit fills lower (the
  reverse for Short); slippage never helps a fill in this model, since
  real slippage is adverse by definition.
- **Commission** subtracts a configurable brokerage cost (a percentage
  of round-trip notional, a flat amount per trade, or both) from every
  trade's pnl.
- **Execution Delay** delays both the entry and exit fill by N candles,
  using the *original* candle series to look up the real close price N
  candles later - a real lookup, not an approximation, which is why
  this is the one perturbation that needs the original candles as an
  extra input (the same pattern `app.trading.analytics.regime_analysis`
  already established for needing candles alongside a `BacktestResult`).
- **Missed Trades** randomly drops each trade independently with a
  configurable probability - a rejected order, a connectivity gap, a
  signal that arrived too late to act on.
- **Position Variation** randomly resizes each trade's quantity within
  a configurable percentage range, simulating imperfect position
  sizing under real execution (partial fills, lot-size rounding,
  capital availability at the moment of entry).

## Trade randomization

Trade Order Shuffle is the only perturbation that reorders the trade
list itself rather than adjusting individual trades - `simulation.py`
builds its equity curve by cumulative pnl *in list order*, not sorted
by each trade's own timestamp, so shuffling the list directly changes
the simulated equity path. This deliberately decouples "does the order
trades occurred in matter to the worst-case drawdown" from "did these
specific trades, at these specific calendar dates, perform well" - the
first is what this perturbation tests; the second is what the original
backtest already answered.

## Slippage modelling

Slippage is applied as a fixed percentage of the fill price, not a
fixed currency amount - a 0.10% slippage on a ₹100 fill costs ₹0.10,
on a ₹1,000 fill it costs ₹1.00. This matches how slippage actually
scales with price in real markets (a wider bid-ask spread on a more
expensive instrument, not a constant absolute cost), and is why
`SlippageConfig` takes `entry_slippage_percent`/`exit_slippage_percent`
rather than a flat amount.

## Execution uncertainty

Execution Delay and Missed Trades both model timing risk, but
differently: a missed trade never happened at all (the position size
becomes irrelevant - it's simply excluded), while a delayed trade still
happened, just later and at a different, real price. Running both
together is meaningful (a real system can both occasionally miss
signals entirely *and* fill the ones it does take a few candles late) -
`PerturbationConfig` supports enabling any combination.

## VaR and CVaR

**Value at Risk (VaR)** at a given confidence level (95% by default)
answers: "with this much confidence, losses will not exceed this
amount." Concretely, it is the *negative* of the return at the
`(100 - confidence)`th percentile of the simulated return distribution
- e.g. at 95% confidence, the 5th-percentile return. If that
percentile return is itself positive (no loss occurs even in the worst
5% of simulations), VaR is reported as 0, not a negative number - "at
risk" only makes sense as a magnitude of possible loss.

**Conditional VaR (CVaR)**, also called Expected Shortfall, answers a
sharper question: "given that we are in that worst-case tail, how bad
is it on average?" It is the *negative* of the mean return across every
simulation at or below the VaR percentile threshold - always at least
as large as VaR itself, since it averages the whole tail rather than
reading one point on it.

Both are computed **non-parametrically**, directly from the simulated
return distribution's own percentiles - no assumption that returns are
normally distributed, which would be an unjustified assumption to make
about a Monte Carlo sample whose shape depends entirely on which
perturbations were enabled.

## Interpreting confidence intervals

The reported confidence interval is the middle `confidence_level`% of
the simulated return distribution (e.g., the 2.5th to 97.5th percentile
for a 95% interval) - a non-parametric range, not a normal-distribution
assumption. A **narrow** interval means the strategy's outcome is
fairly insensitive to the modeled execution uncertainty (reassuring,
but only about the specific perturbations that were turned on). A
**wide** interval means small differences in execution could plausibly
have produced a very different result - treat any single backtest
number as one sample from that wide range, not a forecast, and widen
your position sizing/risk assumptions accordingly.

## Recommended defaults

- **Slippage**: start with the CTO brief's own examples - 0.05% for a
  liquid, high-volume instrument; 0.10% as a reasonable general
  default; 0.25% as a stress-test for a wider spread than usual.
- **Commission**: use your actual broker's published rates, not a
  round number - the whole point is realism.
- **Execution delay**: 1-3 candles is a reasonable starting range for
  a system with modest network/processing latency; more than that
  usually indicates a system design problem worth fixing directly,
  not modeling around.
- **Missed trades**: 1-5% is a reasonable range for occasional
  connectivity/API issues; treat a much higher rate as a sign the
  execution pipeline itself needs attention.
- **Position variation**: ±10-20% covers typical lot-size rounding and
  minor capital-availability effects without swamping the analysis in
  unrealistic sizing swings.
- **Number of simulations**: 100 is a reasonable default for a quick
  check (the CTO brief's own demo uses this); 1,000+ gives smoother,
  more stable percentile estimates (VaR/CVaR/confidence intervals) when
  the analysis matters enough to wait for it.

## Limitations

- **This analysis is only as good as the trades it perturbs.** A
  backtest with very few trades (see `docs/RESEARCH_GUIDE.md`'s own
  sample-size warnings) produces a Monte Carlo distribution built from
  that same small sample - perturbing 3 trades a thousand different
  ways still only explores variations of those 3 trades, not a richer
  underlying reality.
- **Perturbations model plausible uncertainty, not worst-case
  catastrophe.** Nothing here models a broker outage, a flash crash, or
  a total loss of connectivity mid-position - these perturbations
  widen the *realistic* range of outcomes around what actually
  happened, not the full range of everything that could ever go wrong.
- **Trade Order Shuffle assumes trades are exchangeable.** If the
  strategy's edge genuinely depends on *when* in a trend a trade
  occurs (not just that it occurred), shuffling order can understate
  or overstate real path-dependency - read its results as "how
  sequence-sensitive is the drawdown," not as a literal alternate
  history.
- **This is not Walk-Forward Validation.** Monte Carlo perturbs
  execution *outcomes* of trades from one dataset; it says nothing
  about whether the strategy's *parameters* would have been chosen the
  same way, or performed as well, on data it never saw - that question
  belongs to `docs/VALIDATION_GUIDE.md`, not this one.

## Demo

`scripts/demo_monte_carlo.py` runs 100 simulations against a synthetic
backtest with Trade Order Shuffle, 0.10% slippage, and 1% missed
trades enabled, printing the mean return, 95% confidence interval,
worst drawdown, probability of profit, and top risk metrics:

```bash
python3 scripts/demo_monte_carlo.py
```
