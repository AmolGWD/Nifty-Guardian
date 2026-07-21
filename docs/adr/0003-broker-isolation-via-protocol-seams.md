# 0003 - Broker isolation via Protocol seams

## Status

Accepted (established Phases 3-4, held through Phase 10).

## Context

The pre-rebuild codebase imported `kiteconnect` directly across many
modules (`kite_provider.py`, `candle_service.py`, `api.py`, and others),
and at one point printed a raw API key to stdout on import. There was
no single place to fake or mock the broker for tests, and real Zerodha
credentials ended up committed to git history on a working branch
(`debug/signal-runtime`) partly because nothing forced a boundary
between "talks to Kite" and "everything else".

## Decision

Every real call into the KiteConnect SDK is confined to exactly two
files, each hidden behind a `Protocol`:

- `app.kite.service.KiteClientProtocol` (`login_url`, `generate_session`)
  - implemented for real by `app.kite.client`'s factory, faked in tests.
- `app.market_data.client.MarketDataClient` (`get_ltp`,
  `get_historical_data`, `get_instruments`) - implemented for real by
  `KiteMarketDataClient`, faked in tests by `FakeMarketDataClient`.

Nothing under `app/trading/` (indicators, context, conditions,
strategy, risk, decision) imports `app.kite` or `kiteconnect` at all -
confirmed by grep at every phase boundary. The entire trading domain
operates on plain normalized data (`Candle`, `IndicatorSnapshot`, ...),
never on Kite SDK objects.

## Consequences

- Every trading-domain test runs with zero network access and zero
  real credentials - fakes implement the same Protocol, so tests
  exercise the real calling code, not a reimplementation of it.
- A future broker swap (or a second broker) only touches the two
  Protocol-implementing files, not the trading domain.
- Credential handling is centralized enough to reason about: Kite
  session tokens are the only broker secret in the system, and they are
  encrypted at rest (`app/core/security.py`, Fernet) rather than
  handled ad hoc per module.
