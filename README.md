# NIFTY Guardian v2

Trade with Discipline. Not Emotion.

A web application that generates high-confidence paper-trading signals for
NIFTY weekly options using live Zerodha Kite data.

**This application is for paper trading only. There is no automated
real-money trading anywhere in this codebase.**

## Status

Phase 1 — Project Foundation ✅ (backend, frontend, config, logging, health
endpoint, Docker, CI, code quality tooling)

## Roadmap

1. Project foundation (this phase)
2. Core backend architecture — database, SQLAlchemy, DI, repository pattern
3. Zerodha authentication, session and token management
4. Market data layer — spot, option chain, historical candles
5. Indicator engine — EMA, RSI, VWAP, SuperTrend, PCR, OI
6. Signal engine — trading rules, confidence scoring, risk management
7. Paper trading — position management, P&L, trade journal
8. Analytics — performance dashboard, statistics, reports
9. React dashboard — live market view, signal cards, history, charts
10. Telegram notifications, deployment, production hardening

## Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite, Pandas, ta,
KiteConnect SDK, python-dotenv, Pydantic Settings, Uvicorn

**Frontend:** React, Vite, TypeScript

Note: only the dependencies actually used so far (FastAPI, Uvicorn, Pydantic
Settings, python-dotenv on the backend; React, Vite, TypeScript on the
frontend) are installed. SQLAlchemy, Pandas, `ta`, and the KiteConnect SDK
will be added in the phases that need them.

## Project Structure

```
.
├── .github/workflows/ci.yml     # CI: lint, type-check, test, build
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings, loaded from .env
│   │   │   └── logging.py       # Centralized logging configuration
│   │   └── api/
│   │       └── routes/
│   │           └── health.py    # GET /health
│   ├── tests/
│   │   └── test_health.py
│   ├── Dockerfile
│   ├── pyproject.toml           # ruff + mypy + pytest config
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Home page (shows backend connection status)
│   │   ├── main.tsx
│   │   └── env.d.ts             # Typed Vite environment variables
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
├── scripts/
│   ├── dev-backend.sh
│   └── dev-frontend.sh
└── .gitignore
```

## Getting Started

### Backend

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
../scripts/dev-backend.sh
```

The API will be available at `http://localhost:8000`. Check
`http://localhost:8000/health`.

Run tests and code quality checks:

```bash
cd backend
.venv/bin/python -m pytest tests/ -v
.venv/bin/ruff check .
.venv/bin/mypy app
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
../scripts/dev-frontend.sh
```

The app will be available at `http://localhost:5173` and will show the
live backend connection status on load.

Run checks:

```bash
cd frontend
npm run lint
npm run format:check
npm run typecheck
npm run build
```

### Development Scripts

- `scripts/dev-backend.sh` — starts the FastAPI backend with auto-reload.
- `scripts/dev-frontend.sh` — starts the Vite dev server.

Both scripts expect a `.env` file to already exist (copy from `.env.example`
in the corresponding directory) and, for the backend, a `.venv` with
dependencies installed.

### Docker

```bash
docker compose up --build
```

Backend on `http://localhost:8000`, frontend on `http://localhost:5173`.
Requires `backend/.env` to exist first. Note: the Docker build itself was
not verified end-to-end in the development sandbox this project was built
in, because that environment's network policy blocks Docker Hub image
pulls — please verify `docker compose up --build` in an environment with
normal registry access before relying on it.

### CI

`.github/workflows/ci.yml` runs on every push and pull request: backend
lint (ruff), type check (mypy), and tests (pytest); frontend lint (oxlint),
format check (prettier), type check (tsc), and build. All steps were run
locally and pass; the workflow itself has not been observed running on
GitHub Actions yet.

## Configuration

All configuration is read from environment variables. Nothing is
hardcoded. See `backend/.env.example` and `frontend/.env.example` for the
full list of variables and their defaults.

## Security

Never commit `.env`, API keys, passwords, access tokens, TOTP secrets, or
`kite_token.json`. These are all excluded via the root `.gitignore` from
the very first commit of this project.

## Engineering Principles

- SOLID principles and clean architecture (config, logging, and routing
  are separated into their own modules from the start).
- Type hints throughout the Python code (mypy strict mode); TypeScript
  throughout the frontend.
- Logging via the standard `logging` module — no `print()` statements.
- Configuration exclusively from environment variables via Pydantic
  Settings.
- Unit-test friendly structure (see `backend/tests/`).
- Automated linting, formatting, and type checking on every change (ruff,
  mypy, oxlint, prettier), enforced in CI.
