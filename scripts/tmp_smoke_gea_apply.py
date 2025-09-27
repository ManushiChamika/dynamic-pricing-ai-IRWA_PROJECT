from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime
import sys as _Sys0
from pathlib import Path as _Path0
_root0 = _Path0(__file__).resolve().parents[1]
if str(_root0) not in _Sys0.path:
    _Sys0.path.insert(0, str(_root0))

from core.agents.governance_execution_agent import GovernanceExecutionAgent
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic

ROOT = Path(__file__).resolve().parents[1]
MARKET_DB = ROOT / "data" / "market.db"
APP_DB = ROOT / "app" / "data.db"

PRODUCT = "SMOKE-1"
BASE_PRICE = 100.0
NEW_PRICE = 102.0
PROPOSAL_ID = "pp-smoke-1"

def ensure_dirs() -> None:
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "app").mkdir(parents=True, exist_ok=True)

def ensure_settings() -> None:
    conn = sqlite3.connect(APP_DB.as_posix(), timeout=5.0, isolation_level=None)
    try:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        # Minimal guardrails to allow auto-apply
        cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("auto_apply", "true"))
        cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("min_margin", "0.12"))
        cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("max_delta", "0.50"))
        conn.commit()
    finally:
        conn.close()


def seed_market() -> None:
    conn = sqlite3.connect(MARKET_DB.as_posix(), timeout=5.0, isolation_level=None)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
        # Tables used by GEA
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pricing_list (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              product_name TEXT NOT NULL,
              optimized_price REAL NOT NULL,
              last_update TEXT DEFAULT CURRENT_TIMESTAMP,
              reason TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_log (
              proposal_id TEXT PRIMARY KEY,
              product_id TEXT NOT NULL,
              previous_price REAL NOT NULL,
              proposed_price REAL NOT NULL,
              final_price REAL,
              status TEXT NOT NULL,
              actor TEXT NOT NULL,
              reason TEXT,
              received_at TEXT NOT NULL,
              processed_at TEXT
            )
            """
        )
        # Seed pricing_list with base price
        cur.execute("DELETE FROM pricing_list WHERE product_name=?", (PRODUCT,))
        cur.execute(
            "INSERT INTO pricing_list (product_name, optimized_price, last_update, reason) VALUES (?,?,?,?)",
            (PRODUCT, float(BASE_PRICE), datetime.now().isoformat(), "seed"),
        )
        # Clean previous decision_log for this proposal id
        cur.execute("DELETE FROM decision_log WHERE proposal_id=?", (PROPOSAL_ID,))
        conn.commit()
    finally:
        conn.close()


async def run_smoke() -> None:
    agent = GovernanceExecutionAgent()
    await agent.start()
    try:
        payload = {
            "proposal_id": PROPOSAL_ID,
            "product_id": PRODUCT,
            "previous_price": float(BASE_PRICE),
            "proposed_price": float(NEW_PRICE),
        }
        await get_bus().publish(Topic.PRICE_PROPOSAL.value, payload)
        # Allow background thread to finish DB writes
        await asyncio.sleep(1.2)
    finally:
        await agent.stop()


def show_results() -> None:
    conn = sqlite3.connect(MARKET_DB.as_posix(), timeout=5.0)
    try:
        cur = conn.cursor()
        print("-- decision_log rows (most recent 5) --")
        for row in cur.execute(
            "SELECT proposal_id, product_id, previous_price, proposed_price, final_price, status, reason, received_at, processed_at FROM decision_log ORDER BY received_at DESC LIMIT 5"
        ).fetchall():
            print(row)
        print("-- pricing_list row for", PRODUCT, "--")
        row = cur.execute(
            "SELECT product_name, optimized_price, last_update, reason FROM pricing_list WHERE product_name=?",
            (PRODUCT,),
        ).fetchone()
        print(row)
    finally:
        conn.close()


if __name__ == "__main__":
    ensure_dirs()
    ensure_settings()
    seed_market()
    asyncio.run(run_smoke())
    show_results()
