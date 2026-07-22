# NIFTY Guardian — Zerodha Broker Adapter Guide

This guide covers `backend/app/brokers/` (Phase 23) - a broker
connectivity adapter implementing the existing, frozen
`app.paper_trading.broker_interface.BrokerInterface` Protocol against
the real Zerodha Kite Connect API. Broker connectivity only: no new
trading logic, no changes to `app.runtime`, no changes to
`app.trading` (including strategies), no changes to `PaperBroker`. It
does **not** place a real order in this phase - see "Migration to Live
Trading" below for what still needs to happen before it could.

## Architecture

```
                    ┌─────────────────────────┐
                    │      OrderManager        │  (frozen, app.paper_trading)
                    │  only knows BrokerInterface│
                    └────────────┬─────────────┘
                                 │ submit_order(Order) / cancel_order(Order)
                    ┌────────────┴─────────────┐
                    │      BrokerInterface       │  (frozen, Protocol)
                    └──────┬──────────────┬─────┘
                           │              │
                  ┌────────┴───────┐ ┌────┴──────────┐
                  │  PaperBroker    │ │ ZerodhaBroker  │  (this phase)
                  │  (frozen,      │ │                │
                  │   untouched)   │ │                │
                  └────────────────┘ └───────┬────────┘
                                              │ mapper.py (Order <-> Kite params)
                                     ┌────────┴────────┐
                                     │ KiteConnectClient │  (Protocol, interface.py)
                                     └────────┬────────┘
                                              │
                                     ┌────────┴────────┐
                                     │ ZerodhaKiteClient │  (kite_client.py - thin,
                                     │                  │   translates SDK exceptions)
                                     └────────┬────────┘
                                              │
                                     ┌────────┴────────┐
                                     │  KiteConnect SDK  │
                                     └──────────────────┘
```

`OrderManager` (frozen) never knows which `BrokerInterface`
implementation it holds - the same reason `docs/PAPER_TRADING_GUIDE.md`
already documented this seam before either broker beyond `PaperBroker`
existed. Every layer above is a `Protocol` seam for testability:
`BrokerInterface` lets `OrderManager` be tested without a broker at
all; `KiteConnectClient` lets `ZerodhaBroker` be tested without the
real `kiteconnect` SDK (every test in `tests/brokers/` uses a fake
`KiteConnectClient`, never a real network call).

### Files

| File | Responsibility |
|---|---|
| `interface.py` | `KiteConnectClient` Protocol - the one seam to the SDK |
| `models.py` | `BrokerPosition`/`BrokerHolding`/`BrokerProfile`/`BrokerOrder` - new types with no existing equivalent |
| `mapper.py` | Every Kite ↔ internal translation, both directions |
| `errors.py` | `AuthenticationError`/`ConnectionError`/`OrderRejectedError`/`RateLimitError`/`BrokerUnavailableError`/`MappingError` |
| `authentication.py` | `ZerodhaCredentials` (env-loaded), `load_credentials()`, `validate_session()` |
| `kite_client.py` | `ZerodhaKiteClient` (concrete SDK wrapper) + `translate_kite_exception()` |
| `zerodha_broker.py` | `ZerodhaBroker` - implements `BrokerInterface`, plus `get_positions()`/`get_holdings()`/`get_profile()` |

## Authentication flow

Deliberately independent of `app.kite`'s existing OAuth login-flow/
session database (`app.kite.service.KiteAuthService`,
`app.kite.repository.KiteSessionRepository`) - that machinery serves a
different concern (a human logging in through a browser to browse
market data). This adapter is driven by an already-generated access
token, matching how automated trading systems actually use Kite
Connect: a human (or a scheduled job) completes the login flow once
each morning and feeds the resulting access token to this process via
`ZERODHA_ACCESS_TOKEN`, rather than this adapter performing an
interactive login itself.

```
load_credentials()                    # reads ZERODHA_* from the environment
      │                                 raises AuthenticationError if anything
      │                                 required is missing - before any API call
      ▼
build_kite_connect_client()           # KiteConnect(api_key=...).set_access_token(...)
      │
      ▼
ZerodhaKiteClient(kite)                # wraps it behind KiteConnectClient
      │
      ▼
validate_session(client)              # calls profile() - confirms the token is
      │                                 actually valid, eagerly, not on first use
      ▼
ZerodhaBroker(client, ...)             # ready to use
```

`build_zerodha_broker(credentials)` runs this entire chain in one
call. **Session validation is eager**: `validate_session()` calls the
cheapest authenticated endpoint Kite offers (`profile()`) immediately,
so an expired or invalid token surfaces as `AuthenticationError` at
startup, not on whichever trading call happens to run first.

**Zerodha Kite Connect has no refresh-token concept** - access tokens
are valid for exactly one trading day and can only be renewed by a
fresh login (a new `request_token` exchange), never silently
refreshed. `ZerodhaCredentials.refresh_token` exists because the CTO
brief names it ("Refresh Token (if applicable)") - it is honestly
documented as unused rather than faked with a mechanism Kite's real
API doesn't have.

## Mapping philosophy

**No Kite SDK object or raw Kite dict ever crosses out of this
package.** Every field this adapter exposes anywhere else comes from
one of `mapper.py`'s functions.

**Reuse the frozen `Order` type directly - don't invent a duplicate.**
`BrokerInterface.submit_order()`/`cancel_order()` already mandate
`app.paper_trading.models.Order` as both the input and output type -
there is no separate "internal Order" to design. A full Kite order
response cannot become an `Order` on its own, though:
`strategy_name`/`stop_loss`/`target` are this codebase's own fields,
never returned by Zerodha's API. `map_kite_order_update(original,
kite_order)` therefore takes the *original* internal `Order` and
merges Kite's status/fill data onto it via `model_copy()` - the exact
pattern `OrderManager._transition()` (frozen) already uses for every
other order state change.

**`BrokerPosition`/`BrokerHolding` are new types, not a repurposing of
`app.paper_trading.models.Position`.** A live broker position is a
different concept from a paper-trading `Position`: the latter is a
stateful value `PositionManager` owns and transitions through
`OPEN`/`PARTIALLY_EXITED`/`CLOSED` for one paper strategy's trade - it
has no equivalent for `product`/`last_price`/exchange, and Zerodha's
position query has no `strategy_name` or status-transition-table
concept at all. A broker "holding" (long-term stock/ETF holdings,
distinct from an intraday/derivatives position) had no existing type
anywhere in this codebase. Both are new, read-only value types this
adapter alone owns.

**Kite's order-status vocabulary is richer than this codebase's
`OrderStatus`.** Every Kite pending/intermediate status (`OPEN`,
`TRIGGER PENDING`, `OPEN PENDING`, `VALIDATION PENDING`, `MODIFY
PENDING`, `PUT ORDER REQ RECEIVED`, `AMO REQ RECEIVED`) collapses to
`SUBMITTED` - an explicit, documented simplification in
`mapper._KITE_STATUS_TO_INTERNAL`, not a silently dropped distinction.
An unrecognized status raises `MappingError` rather than guessing.

**Direction mapping is a simplification, honestly flagged.**
`StrategyDirection.LONG`/`SHORT` maps to Kite's `transaction_type`
`BUY`/`SELL` - accurate for opening a position, but a `SELL` can also
mean *exiting* a long position, not necessarily entering a short one.
This mapping is presentational/translation only (no trading decision
is made here), and the ambiguity is exactly the kind of nuance Live
Trading Mode's real order-flow wiring will need to resolve with actual
position-aware context - not something this adapter phase can or
should decide.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `ZERODHA_API_KEY` | Yes | Kite Connect app API key |
| `ZERODHA_API_SECRET` | Yes | Kite Connect app API secret |
| `ZERODHA_ACCESS_TOKEN` | Yes | Today's access token (from a completed login flow) |
| `ZERODHA_BASE_URL` | No | Override the Kite API base URL (defaults to the SDK's own) |

Loaded via `ZerodhaCredentials` (`pydantic_settings.BaseSettings`,
`env_prefix="ZERODHA_"`) - the same convention
`app.core.config.Settings` already uses, deliberately kept as a
separate settings class (a separate credential set from `app.kite`'s
`KITE_API_KEY`/`KITE_API_SECRET`, which serve the browser login flow).
Never hardcoded anywhere - `load_credentials()` raises
`AuthenticationError` naming every missing variable if any required
value isn't set.

## Error handling

Every `kiteconnect.exceptions.KiteException` subclass is translated by
`kite_client.translate_kite_exception()` into exactly one of six typed
exceptions - callers never catch a raw SDK exception:

| Kite exception | → | Internal exception |
|---|---|---|
| `TokenException`, `PermissionException` | → | `AuthenticationError` |
| `NetworkException` | → | `ConnectionError` |
| `OrderException` | → | `OrderRejectedError` |
| `InputException` | → | `MappingError` |
| `GeneralException`, `DataException` | → | `BrokerUnavailableError` |
| any exception with `.code == 429` | → | `RateLimitError` (checked first, regardless of subclass) |

`MappingError` is also raised directly by this adapter's own code (not
just SDK-exception translation) whenever a Kite payload is missing an
expected field, or when `ZerodhaBroker.submit_order()` has no
`trading_symbol_resolver` configured (see below) - it always means
*this adapter's* translation layer refused to guess, never a
broker-side failure.

## One deliberate, honestly-flagged limitation

`app.paper_trading.models.Order` (frozen) carries no instrument
identifier - `PaperBroker` never needed one, since it simulates a fill
in the abstract without knowing which real contract it's for. A real
Zerodha order absolutely needs a trading symbol + exchange to know
*what* to buy. Resolving "which real NIFTY options contract does this
`Order` correspond to" is explicitly Live Trading Mode's job (the
next, not-yet-authorized phase), not this adapter's - modifying the
frozen `Order` to add a symbol field would itself be a Runtime/
paper_trading change, forbidden this phase.

`ZerodhaBroker`'s constructor accepts a `trading_symbol_resolver:
Callable[[Order], str]` for exactly this seam. Its default
implementation raises `MappingError` loudly and immediately, naming
the order, rather than silently guessing a wrong symbol - "broker
connectivity only" means this phase makes that gap impossible to miss
rather than papering over it.

## Demo

`scripts/demo_zerodha_adapter.py` demonstrates authentication, fetching
a profile, mapping an order, mapping a position, and handling an error
- entirely against mocked Kite responses, no real credentials, no real
API calls:

```bash
python3 scripts/demo_zerodha_adapter.py
```

## Migration to Live Trading

Nothing about `OrderManager` or any other frozen `app.paper_trading`
component changes when `ZerodhaBroker` replaces `PaperBroker` - that's
the entire point of `BrokerInterface`. What Live Trading Mode (the
next, not-yet-authorized phase) still needs to add:

1. **A real `trading_symbol_resolver`** - resolving a strategy's
   intended NIFTY options contract (strike, expiry, CE/PE) into a Kite
   trading symbol. This needs option-chain/expiry data
   (`app.market_data`, frozen) and is a strategy/runtime-layer
   decision, not something this adapter package should own.
2. **Wiring `ZerodhaBroker` into `app.runtime`'s startup** in place of
   (or alongside) `PaperBroker` - a configuration choice at the
   `RuntimeContext` construction site, not a change to `RuntimeEngine`
   or `EventProcessor` themselves.
3. **A real capital/margin check against `get_positions()`/
   `get_holdings()`** before placing a live order - this phase exposes
   both as read methods but nothing yet calls them as part of a
   pre-trade check.
4. **Handling asynchronous fills** - `PaperBroker` always fills
   synchronously and completely; a real order can partially fill or
   sit pending, and `docs/PAPER_TRADING_GUIDE.md`'s own "Migration path
   to Live Broker" section already anticipated this: a live adapter
   needs to call back into `OrderManager` as fills arrive, rather than
   returning a final `Order` synchronously the way this phase's
   `submit_order()` still does (via an immediate `order_history()`
   lookup, which is only a reasonable approximation for a fast-filling
   market order).
5. **Explicit, deliberate sign-off before any real order is ever
   placed** - this phase's `ZerodhaBroker` is fully wired and tested
   against mocked Kite responses only; nothing in this repository has
   called it against the real Kite Connect API.
