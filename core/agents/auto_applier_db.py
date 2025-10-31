from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutoApplierDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path.as_posix(), check_same_thread=False)

    def load_settings(self) -> tuple[bool, float, float]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
            defaults = {
                "auto_apply": "false",
                "min_margin": "0.12",
                "max_delta": "0.10",
            }
            for k, v in defaults.items():
                cur.execute("SELECT value FROM settings WHERE key=?", (k,))
                if cur.fetchone() is None:
                    cur.execute("INSERT INTO settings (key, value) VALUES (?,?)", (k, v))
            conn.commit()
            cur.execute("SELECT key, value FROM settings")
            kv = {k: (v or "") for k, v in cur.fetchall()}
            auto_apply = str(kv.get("auto_apply", defaults["auto_apply"])).strip().lower() == "true"
            try:
                min_margin = float(kv.get("min_margin", defaults["min_margin"]))
            except Exception:
                min_margin = float(defaults["min_margin"])
            try:
                max_delta = float(kv.get("max_delta", defaults["max_delta"]))
            except Exception:
                max_delta = float(defaults["max_delta"])
            return auto_apply, min_margin, max_delta
        finally:
            conn.close()

    def insert_decision(
        self,
        sku: str,
        old_price: Optional[float],
        new_price: float,
        margin: Optional[float],
        algorithm: Optional[str],
        decision: str,
        actor: str,
        proposal_id: Optional[str] = None,
    ) -> None:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_log (
                  id TEXT PRIMARY KEY,
                  proposal_id TEXT,
                  sku TEXT NOT NULL,
                  old_price REAL,
                  new_price REAL NOT NULL,
                  margin REAL,
                  algorithm TEXT,
                  decision TEXT NOT NULL,
                  actor TEXT NOT NULL,
                  ts TEXT NOT NULL
                )
                """
            )
            cur.execute(
                "INSERT INTO decision_log (id, proposal_id, sku, old_price, new_price, margin, algorithm, decision, actor, ts)\n"
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    proposal_id,
                    sku,
                    old_price,
                    new_price,
                    margin,
                    algorithm,
                    decision,
                    actor,
                    _utc_now_iso(),
                ),
            )
            conn.commit()
        except Exception as e:
            try:
                print(f"[AutoApplierDB] decision_log insert failed: {e}")
            except Exception:
                pass
        finally:
            conn.close()

    def get_old_price(self, sku: str) -> Optional[float]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS pricing_list (\n"
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                "  product_name TEXT NOT NULL,\n"
                "  optimized_price REAL NOT NULL,\n"
                "  last_update TEXT DEFAULT CURRENT_TIMESTAMP,\n"
                "  reason TEXT\n"
                ")"
            )
            cur.execute("SELECT optimized_price FROM pricing_list WHERE product_name=?", (sku,))
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else None
        except Exception:
            return None
        finally:
            conn.close()

    def get_proposal_id(self, sku: str, proposed_price: float) -> Optional[str]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS price_proposals (
                  id TEXT PRIMARY KEY,
                  sku TEXT,
                  proposed_price REAL,
                  current_price REAL,
                  margin REAL,
                  algorithm TEXT,
                  ts TEXT
                )
                """
            )
            cur.execute(
                "SELECT id FROM price_proposals WHERE sku=? AND proposed_price=? ORDER BY ts DESC LIMIT 1",
                (sku, proposed_price),
            )
            row = cur.fetchone()
            return row[0] if row else None
        except Exception:
            return None
        finally:
            conn.close()

    def apply_price_atomic(
        self,
        market_db_path: Path,
        sku: str,
        proposed_price: float,
        margin: Optional[float],
        algorithm: Optional[str],
        proposal_id: Optional[str],
        current_price: Optional[float],
    ) -> bool:
        conn = None
        try:
            conn = sqlite3.connect(self.db_path.as_posix(), check_same_thread=False, isolation_level=None)
            cur = conn.cursor()
            esc = market_db_path.as_posix().replace("'", "''")
            cur.execute(f"ATTACH DATABASE '{esc}' AS market")
            cur.execute(
                "CREATE TABLE IF NOT EXISTS decision_log (\n"
                "  id TEXT PRIMARY KEY,\n"
                "  proposal_id TEXT,\n"
                "  sku TEXT NOT NULL,\n"
                "  old_price REAL,\n"
                "  new_price REAL NOT NULL,\n"
                "  margin REAL,\n"
                "  algorithm TEXT,\n"
                "  decision TEXT NOT NULL,\n"
                "  actor TEXT NOT NULL,\n"
                "  ts TEXT NOT NULL\n"
                ")"
            )
            cur.execute(
                "CREATE TABLE IF NOT EXISTS market.pricing_list (\n"
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                "  product_name TEXT NOT NULL,\n"
                "  optimized_price REAL NOT NULL,\n"
                "  last_update TEXT DEFAULT CURRENT_TIMESTAMP,\n"
                "  reason TEXT\n"
                ")"
            )
            cur.execute("BEGIN IMMEDIATE")
            cur.execute("SELECT optimized_price FROM market.pricing_list WHERE product_name=?", (sku,))
            row_old = cur.fetchone()
            old_price = float(row_old[0]) if row_old and row_old[0] is not None else (float(current_price) if current_price is not None else None)
            if row_old and row_old[0] is not None:
                try:
                    if float(row_old[0]) == proposed_price:
                        self.insert_decision(
                            sku=sku,
                            old_price=old_price,
                            new_price=proposed_price,
                            margin=margin,
                            algorithm=algorithm,
                            decision="AUTO_APPLIED",
                            actor="governance",
                            proposal_id=proposal_id,
                        )
                        cur.execute("ROLLBACK")
                        return True
                except Exception:
                    pass
            try:
                cur.execute(
                    "INSERT INTO decision_log (id, proposal_id, sku, old_price, new_price, margin, algorithm, decision, actor, ts)\n"
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        str(uuid.uuid4()),
                        proposal_id,
                        sku,
                        old_price,
                        proposed_price,
                        margin,
                        algorithm,
                        "AUTO_APPLIED",
                        "governance",
                        _utc_now_iso(),
                    ),
                )
            except Exception:
                pass
            cur.execute(
                "SELECT 1 FROM market.pricing_list WHERE product_name=?",
                (sku,),
            )
            exists_m = cur.fetchone() is not None
            if exists_m:
                cur.execute(
                    "UPDATE market.pricing_list SET optimized_price=?, last_update=CURRENT_TIMESTAMP, reason=? WHERE product_name=?",
                    (proposed_price, "auto_applied(governance)", sku),
                )
            else:
                cur.execute(
                    "INSERT INTO market.pricing_list (product_name, optimized_price, last_update, reason) VALUES (?,?,CURRENT_TIMESTAMP,?)",
                    (sku, proposed_price, "auto_applied(governance)"),
                )
            cur.execute("COMMIT")
            return True
        except Exception as e:
            try:
                if conn:
                    conn.execute("ROLLBACK")
            except Exception:
                pass
            try:
                print(f"[AutoApplierDB] apply_price_atomic error: {e}")
            except Exception:
                pass
            return False
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
