# Sample dataset

`nifty_sample_candles.csv` is the one canonical copy of the runtime's
default 75-candle replay dataset - used by `app.api.dashboard.
dashboard_service` and `app.api.signals.signals_service` (the deployed
backend), and by every local demo script under `scripts/` (e.g.
`scripts/demo_backtest.py`) that needs the same data.

It lives here, inside the `app` package, rather than at the repo-root
`scripts/sample_data/` (where the other sample datasets still live),
because `backend/Dockerfile` only ever `COPY app ./app` - a typical
Railway deployment's build context is `backend/` itself, so `scripts/`
(a sibling of `backend/`, outside that build context) is never present
in the deployed container, and Docker has no way to `COPY` a path from
outside its build context. This file used to live only at
`scripts/sample_data/nifty_sample_candles.csv`; it was moved here (not
duplicated) specifically to fix that deployment failure - see
`app.api.dashboard.dashboard_service`'s own `_SAMPLE_DATASET_PATH`
comment.
