"""
========================================
 NIFTY Guardian Paper Trade Service
========================================

Persistence and lifecycle bookkeeping for paper trades only.

This service never decides when a trade should be opened, monitored,
or closed - that decision belongs to the paper trade orchestrator.
It only records what it is told and reports it back.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.config.settings import DATABASE_URL


def _resolve_db_path(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url[len("sqlite:///"):]
    return database_url


class PaperTradeService:

    def __init__(self, database_url: str = DATABASE_URL):
        self.db_path = _resolve_db_path(database_url)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_number INTEGER NOT NULL,
                    option_type TEXT NOT NULL,
                    strike INTEGER NOT NULL,
                    expiry TEXT NOT NULL,
                    entry_spot REAL NOT NULL,
                    entry_premium REAL NOT NULL,
                    exit_spot REAL,
                    exit_premium REAL,
                    quantity INTEGER NOT NULL,
                    stop_loss REAL,
                    target1 REAL,
                    target2 REAL,
                    confidence INTEGER,
                    guardian_score INTEGER,
                    indicator_snapshot TEXT,
                    status TEXT NOT NULL,
                    exit_reason TEXT,
                    pnl REAL,
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (trade_id) REFERENCES paper_trades (id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_trades INTEGER NOT NULL DEFAULT 0,
                    open_count INTEGER NOT NULL DEFAULT 0,
                    closed_count INTEGER NOT NULL DEFAULT 0,
                    wins INTEGER NOT NULL DEFAULT 0,
                    losses INTEGER NOT NULL DEFAULT 0,
                    total_pnl REAL NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute("INSERT OR IGNORE INTO trade_state (id) VALUES (1)")
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------
    # Create
    # ------------------------------------------------------------

    def create_trade(self, trade_data: dict) -> dict:
        now = datetime.now().isoformat(timespec="seconds")

        conn = self._connect()
        try:
            trade_number = conn.execute(
                "SELECT COUNT(*) AS c FROM paper_trades"
            ).fetchone()["c"] + 1

            cursor = conn.execute(
                """
                INSERT INTO paper_trades (
                    trade_number, option_type, strike, expiry,
                    entry_spot, entry_premium, quantity,
                    stop_loss, target1, target2,
                    confidence, guardian_score, indicator_snapshot,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
                """,
                (
                    trade_number,
                    trade_data["option_type"],
                    trade_data["strike"],
                    trade_data["expiry"],
                    trade_data["entry_spot"],
                    trade_data["entry_premium"],
                    trade_data["quantity"],
                    trade_data.get("stop_loss"),
                    trade_data.get("target1"),
                    trade_data.get("target2"),
                    trade_data.get("confidence"),
                    trade_data.get("guardian_score"),
                    json.dumps(trade_data.get("indicator_snapshot") or {}),
                    now,
                ),
            )
            trade_id = cursor.lastrowid

            self._record_event(conn, trade_id, "TRADE_OPENED", trade_data)

            conn.execute(
                """
                UPDATE trade_state
                SET total_trades = total_trades + 1,
                    open_count = open_count + 1
                WHERE id = 1
                """
            )

            conn.commit()
            return self._get_trade(conn, trade_id)
        finally:
            conn.close()

    # ------------------------------------------------------------
    # Update (monitoring snapshot, no state transition)
    # ------------------------------------------------------------

    def update_trade(self, trade_id: int, updates: dict) -> dict:
        conn = self._connect()
        try:
            self._record_event(conn, trade_id, "TRADE_MONITORED", updates)
            conn.commit()
            return self._get_trade(conn, trade_id)
        finally:
            conn.close()

    # ------------------------------------------------------------
    # Close
    # ------------------------------------------------------------

    def close_trade(self, trade_id: int, exit_data: dict) -> dict:
        now = datetime.now().isoformat(timespec="seconds")

        conn = self._connect()
        try:
            trade = conn.execute(
                "SELECT * FROM paper_trades WHERE id = ?", (trade_id,)
            ).fetchone()

            if trade is None:
                raise ValueError(f"Paper trade {trade_id} not found")

            if trade["status"] == "CLOSED":
                return self._row_to_dict(trade)

            entry_premium = trade["entry_premium"]
            exit_premium = exit_data["exit_premium"]
            quantity = trade["quantity"]
            pnl = round((exit_premium - entry_premium) * quantity, 2)
            is_win = 1 if pnl > 0 else 0

            conn.execute(
                """
                UPDATE paper_trades
                SET exit_spot = ?, exit_premium = ?, pnl = ?,
                    status = 'CLOSED', exit_reason = ?, closed_at = ?
                WHERE id = ?
                """,
                (
                    exit_data.get("exit_spot"),
                    exit_premium,
                    pnl,
                    exit_data.get("exit_reason"),
                    now,
                    trade_id,
                ),
            )

            self._record_event(conn, trade_id, "TRADE_CLOSED", {**exit_data, "pnl": pnl})

            conn.execute(
                """
                UPDATE trade_state
                SET open_count = open_count - 1,
                    closed_count = closed_count + 1,
                    wins = wins + ?,
                    losses = losses + ?,
                    total_pnl = total_pnl + ?
                WHERE id = 1
                """,
                (is_win, 1 - is_win, pnl),
            )

            conn.commit()
            return self._get_trade(conn, trade_id)
        finally:
            conn.close()

    # ------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------

    def get_open_trades(self) -> list:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM paper_trades WHERE status = 'OPEN' ORDER BY id DESC"
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def get_closed_trades(self) -> list:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM paper_trades WHERE status = 'CLOSED' ORDER BY id DESC"
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def get_summary(self) -> dict:
        conn = self._connect()
        try:
            state = conn.execute("SELECT * FROM trade_state WHERE id = 1").fetchone()
            summary = dict(state) if state else {}
            closed = summary.get("closed_count") or 0
            wins = summary.get("wins") or 0
            summary["win_rate"] = round((wins / closed) * 100, 2) if closed > 0 else 0
            return summary
        finally:
            conn.close()

    # ------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------

    def _get_trade(self, conn, trade_id: int) -> dict:
        row = conn.execute(
            "SELECT * FROM paper_trades WHERE id = ?", (trade_id,)
        ).fetchone()
        return self._row_to_dict(row)

    def _record_event(self, conn, trade_id: int, event_type: str, details: dict):
        conn.execute(
            """
            INSERT INTO trade_events (trade_id, event_type, details, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                trade_id,
                event_type,
                json.dumps(details, default=str),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

    @staticmethod
    def _row_to_dict(row) -> dict:
        if row is None:
            return {}

        data = dict(row)

        if data.get("indicator_snapshot"):
            try:
                data["indicator_snapshot"] = json.loads(data["indicator_snapshot"])
            except (TypeError, ValueError):
                pass

        return data


paper_trade_service = PaperTradeService()
