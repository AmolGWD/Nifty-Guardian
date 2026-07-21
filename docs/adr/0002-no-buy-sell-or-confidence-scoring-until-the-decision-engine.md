# 0002 - No BUY/SELL or confidence scoring until the Decision Engine

## Status

Accepted (established Phase 6, held through Phase 10).

## Context

The pre-rebuild `debug/signal-runtime` branch computed a single 0-100
"confidence" score (`score_engine.py`) from a weighted rule pass count,
then mapped score thresholds directly onto a `"BUY CE"` / `"BUY PE"` /
`"WAIT"` / `"NO TRADE"` signal (`decision_engine.py`) in the same pass.
Market description, technical confirmation, and the trade decision were
one inseparable calculation - there was no way to inspect *why* a
number came out the way it did, or to reuse the market read for
anything other than that one scoring formula.

## Decision

No package below the Decision Engine (`app/trading/context/`,
`conditions/`, `strategy/`, `risk/`) is allowed to emit a BUY/SELL-style
decision or a numeric confidence percentage. Instead:

- Classification packages (`context/`, `conditions/`) emit categorical,
  deterministic enums (`TrendContext`, `Bias`, `NoTradeReason`, ...).
- `strategy/` emits a categorical `direction` (`Long`/`Short`/`None`)
  and a categorical `strength` (`Strong`/`Moderate`/`Weak`) per
  strategy, not a score.
- `risk/` emits `risk_ok` (a boolean gate) plus concrete numeric risk
  figures (position size, stop-loss, target) - never a probability of
  success.
- Only `decision/` (Phase 10) combines these into a single
  `recommended` boolean and a `selected_strategy`, and even then
  produces no numeric confidence - `recommendation_strength` remains
  categorical.

Confirmed by grep at every phase boundary: no occurrence of "buy",
"sell", "confidence", or "probability" in actual code anywhere under
`app/trading/`, only in docstrings explaining what is deliberately
avoided.

## Consequences

- Every intermediate stage stays inspectable and independently useful -
  `MarketContext` or `TradingConditions` could serve a dashboard or a
  different strategy without dragging a scoring formula along.
- Adding a second strategy (beyond Phase 8's EMA Breakout) does not
  require redesigning a shared scoring formula - it only needs to
  implement the same `Strategy` interface.
- The trade-off: no single number exists to rank "how good" a setup is
  end-to-end. That is an explicit, not accidental, gap - if numeric
  confidence is wanted later, it is new, clearly-scoped work on top of
  the Decision Engine, not a retrofit into the categorical layers.
