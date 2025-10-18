from __future__ import annotations

import asyncio
import threading
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic
from core.payloads import PriceProposalPayload, PriceUpdatePayload
from core.observability.logging import get_logger


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _market_db_path() -> Path:
    return Path(__file__).resolve().parents[2] / "app" / "data.db"


def _app_db_path() -> Path:
    return Path(__file__).resolve().parents[2] / "app" / "data.db"


@dataclass
class Guardrails:
    auto_apply: bool
    min_margin: float
    max_delta: float


class GovernanceExecutionAgent:
    def __init__(self) -> None:
        self._callback = None

    async def start(self) -> None:
        async def on_price_proposal(payload: Dict[str, Any]):
            try:
                self._handle_price_proposal(payload)  # offload inside
            except Exception as e:
                try:
                    get_logger("ge_agent").warning("on_price_proposal_error", error=str(e))
                except Exception:
                    print(f"Failed to log price proposal error: {e}")

        self._callback = on_price_proposal
        get_bus().subscribe(Topic.PRICE_PROPOSAL.value, self._callback)
        try:
            get_logger("ge_agent").info("subscribed", topic=Topic.PRICE_PROPOSAL.value)
        except Exception as e:
            print(f"Failed to log subscription: {e}")

    async def stop(self) -> None:
        self._callback = None

    # ---------- internals ----------
    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        cur = conn.cursor()
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
              status TEXT NOT NULL CHECK (status IN (
                'RECEIVED', 'APPROVED', 'REJECTED', 'APPLIED_AUTO', 'APPLY_FAILED', 'STALE'
              )),
              actor TEXT NOT NULL,
              reason TEXT,
              received_at TEXT NOT NULL,
              processed_at TEXT
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_decision_log_product_id ON decision_log(product_id)"
        )

    def _load_guardrails(self) -> Guardrails:
        auto_apply = False
        min_margin = 0.12
        max_delta = 0.10
        try:
            conn = sqlite3.connect(_app_db_path().as_posix(), timeout=5.0)
            try:
                cur = conn.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
                defaults = {
                    "auto_apply": "false",
                    "min_margin": str(min_margin),
                    "max_delta": str(max_delta),
                }
                for k, v in defaults.items():
                    cur.execute("SELECT value FROM settings WHERE key=?", (k,))
                    if cur.fetchone() is None:
                        cur.execute("INSERT INTO settings (key, value) VALUES (?,?)", (k, v))
                conn.commit()
                cur.execute("SELECT key, value FROM settings")
                kv = {k: (v or "") for k, v in cur.fetchall()}
                auto_apply = str(kv.get("auto_apply", "false")).strip().lower() == "true"
                try:
                    min_margin = float(kv.get("min_margin", str(min_margin)))
                except (ValueError, TypeError):
                    pass
                try:
                    max_delta = float(kv.get("max_delta", str(max_delta)))
                except (ValueError, TypeError):
                    pass
            finally:
                conn.close()
        except Exception:
            pass
        return Guardrails(auto_apply=auto_apply, min_margin=min_margin, max_delta=max_delta)

    def _handle_price_proposal(self, payload: Dict[str, Any]) -> None:
        # Validate payload shape
        try:
            pp = PriceProposalPayload(
                proposal_id=str(payload["proposal_id"]),
                product_id=str(payload["product_id"]),
                previous_price=float(payload["previous_price"]),
                proposed_price=float(payload["proposed_price"]),
            )
        except (KeyError, ValueError, TypeError) as e:
            try:
                get_logger("ge_agent").warning("invalid_payload", error=str(e), payload=payload)
            except Exception:
                print(f"Failed to log invalid payload: {e}")
            return

        # Offload to background thread to avoid blocking bus
        threading.Thread(target=lambda: self._apply_sync(pp), daemon=True).start()

    def _apply_sync(self, pp: PriceProposalPayload) -> None:
        guards = self._load_guardrails()
        if not guards.auto_apply:
            # Log RECEIVED but do not apply
            self._log_received_only(pp, actor="governance", reason="auto_apply disabled")
            return

        mpath = _market_db_path().as_posix()
        conn = sqlite3.connect(mpath, timeout=5.0, isolation_level=None)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=5000")
            self._ensure_schema(conn)

            # Idempotent insert
            cur.execute(
                """
                INSERT OR IGNORE INTO decision_log (
                  proposal_id, product_id, previous_price, proposed_price, final_price, status, actor, reason, received_at, processed_at
                ) VALUES (?,?,?,?,NULL, 'RECEIVED', ?, NULL, ?, NULL)
                """,
                (pp["proposal_id"], pp["product_id"], pp["previous_price"], pp["proposed_price"], "governance", _utc_now_iso()),
            )

            # Read current state
            cur.execute("SELECT status FROM decision_log WHERE proposal_id=?", (pp["proposal_id"],))
            row = cur.fetchone()
            if not row:
                return
            status = row[0]
            if status != "RECEIVED":
                return

            # Guardrail checks
            # Fetch current price from pricing_list
            cur.execute("SELECT optimized_price FROM pricing_list WHERE product_name=?", (pp["product_id"],))
            rowp = cur.fetchone()
            current_price = float(rowp[0]) if rowp and rowp[0] is not None else None
            prev = float(pp["previous_price"]) if pp["previous_price"] is not None else None
            base = prev if prev is not None else (current_price if current_price is not None else 0.0)
            try:
                delta_pct = abs(float(pp["proposed_price"]) - float(base)) / float(base) if base else 0.0
            except Exception:
                delta_pct = 0.0
            if delta_pct > guards.max_delta:
                cur.execute(
                    "UPDATE decision_log SET status='REJECTED', reason=?, processed_at=? WHERE proposal_id=? AND status='RECEIVED'",
                    (f"delta {delta_pct:.2%} exceeds max_delta {guards.max_delta:.2%}", _utc_now_iso(), pp["proposal_id"]),
                )
                conn.commit()
                return

            # Apply with optimistic concurrency
            try:
                cur.execute("BEGIN IMMEDIATE")
                cur.execute(
                    "UPDATE pricing_list SET optimized_price=?, last_update=CURRENT_TIMESTAMP, reason=? WHERE product_name=? AND optimized_price=?",
                    (
                        float(pp["proposed_price"]),
                        "auto_applied(governance)",
                        pp["product_id"],
                        float(pp["previous_price"]),
                    ),
                )
                rows = cur.rowcount if hasattr(cur, "rowcount") else cur.execute("SELECT changes()" ).fetchone()[0]
                if rows and rows > 0:
                    # success
                    cur.execute(
                        "UPDATE decision_log SET final_price=?, status='APPLIED_AUTO', processed_at=? WHERE proposal_id=?",
                        (float(pp["proposed_price"]), _utc_now_iso(), pp["proposal_id"]),
                    )
                    cur.execute("COMMIT")
                    conn.commit()
                    # publish price.update
                    upd: PriceUpdatePayload = {
                        "proposal_id": pp["proposal_id"],
                        "product_id": pp["product_id"],
                        "final_price": float(pp["proposed_price"]),
                    }
                    self._publish_update_async(upd)
                    try:
                        get_logger("ge_agent").info(
                            "applied_auto",
                            product_id=pp["product_id"],
                            proposal_id=pp["proposal_id"],
                            final_price=float(pp["proposed_price"]),
                        )
                    except Exception:
                        pass
                else:
                    # stale
                    cur.execute(
                        "UPDATE decision_log SET status='STALE', reason=?, processed_at=? WHERE proposal_id=?",
                        ("base price changed", _utc_now_iso(), pp["proposal_id"]),
                    )
                    cur.execute("COMMIT")
                    conn.commit()
            except sqlite3.OperationalError as e:
                try:
                    cur.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                try:
                    cur.execute(
                        "UPDATE decision_log SET status='APPLY_FAILED', reason=?, processed_at=? WHERE proposal_id=? AND status='RECEIVED'",
                        (str(e), _utc_now_iso(), pp["proposal_id"]),
                    )
                    conn.commit()
                except sqlite3.Error:
                    pass
            except Exception as e:
                try:
                    cur.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                try:
                    cur.execute(
                        "UPDATE decision_log SET status='APPLY_FAILED', reason=?, processed_at=? WHERE proposal_id=? AND status='RECEIVED'",
                        (str(e), _utc_now_iso(), pp["proposal_id"]),
                    )
                    conn.commit()
                except sqlite3.Error:
                    pass
                try:
                    get_logger("ge_agent").warning("apply_failed", error=str(e), proposal_id=pp["proposal_id"], product_id=pp["product_id"])
                except Exception:
                    print(f"Failed to log apply failure: {e}")
            finally:
                try:
                    conn.close()
                except sqlite3.Error:
                    pass

        except (sqlite3.Error, OSError):
            pass

    def _log_received_only(self, pp: PriceProposalPayload, actor: str, reason: Optional[str]) -> None:
        mpath = _market_db_path().as_posix()
        conn = sqlite3.connect(mpath, timeout=5.0, isolation_level=None)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=5000")
            self._ensure_schema(conn)
            cur.execute(
                "INSERT OR IGNORE INTO decision_log (proposal_id, product_id, previous_price, proposed_price, final_price, status, actor, reason, received_at, processed_at) VALUES (?,?,?,?,NULL,'RECEIVED',?,?,?,NULL)",
                (pp["proposal_id"], pp["product_id"], pp["previous_price"], pp["proposed_price"], actor, reason, _utc_now_iso()),
            )
            conn.commit()
        finally:
            try:
                conn.close()
            except sqlite3.Error:
                pass

    def _publish_update_async(self, upd: PriceUpdatePayload) -> None:
        async def _pub():
            try:
                await get_bus().publish(Topic.PRICE_UPDATE.value, upd)
            except Exception as e:
                try:
                    get_logger("ge_agent").warning("publish_update_failed", error=str(e))
                except Exception:
                    print(f"Failed to log publish failure: {e}")
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_pub())
        except RuntimeError:
            threading.Thread(target=lambda: asyncio.run(_pub()), daemon=True).start()
