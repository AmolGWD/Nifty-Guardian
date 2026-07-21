# NIFTY Guardian v2

Trade with Discipline. Not Emotion.

A web application that generates high-confidence trading signals for NIFTY
weekly options using live Zerodha market data.

**This application is for paper trading only. There is no automated
real-money trading anywhere in this codebase.**

## Status

Milestone 1 — Project Foundation ✅

## Scope (full project roadmap)

- Live Market Data
- Technical Indicators
- Signal Engine
- Paper Trading
- Trade History
- Performance Analytics
- Telegram Notifications
- React Dashboard

Milestone 1 covers only the project foundation (this document). Later
milestones will build out the rest, one at a time.

## Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite, Pandas, ta,
KiteConnect SDK, python-dotenv, Pydantic Settings, Uvicorn

**Frontend:** React, Vite, TypeScript

Note: only the dependencies actually used by Milestone 1 (FastAPI, Uvicorn,
Pydantic Settings, python-dotenv on the backend; React, Vite, TypeScript on
the frontend) are installed so far. SQLAlchemy, Pandas, `ta`, and the
KiteConnect SDK will be added when the milestones that need them arrive.

## Project Structure

```
.
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
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Home page (shows backend connection status)
│   │   ├── main.tsx
│   │   └── env.d.ts             # Typed Vite environment variables
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

Run tests:

```bash
cd backend
.venv/bin/python -m pytest tests/ -v
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

### Development Scripts

- `scripts/dev-backend.sh` — starts the FastAPI backend with auto-reload.
- `scripts/dev-frontend.sh` — starts the Vite dev server.

Both scripts expect a `.env` file to already exist (copy from `.env.example`
in the corresponding directory) and, for the backend, a `.venv` with
dependencies installed.

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
- Type hints throughout the Python code; TypeScript throughout the
  frontend.
- Logging via the standard `logging` module — no `print()` statements.
- Configuration exclusively from environment variables via Pydantic
  Settings.
- Unit-test friendly structure (see `backend/tests/`).
