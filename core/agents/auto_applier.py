from __future__ import annotations

import asyncio
import threading
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timezone
import uuid
from typing import Optional

# Migrate to the shared agent SDK bus/protocol/models
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic
from core.agents.agent_sdk.events_models import PriceProposal


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutoApplier:
    """Governance & Execution Agent for PRICE_PROPOSAL events.

    Subscribes to PRICE_PROPOSAL and evaluates merchant guardrails stored in
    app/data.db `settings` table with keys:
      - auto_apply: 'true' | 'false'
      - min_margin: float as string
      - max_delta: float as string (relative allowed change vs current_price)

    Behavior:
      - Always logs a decision into app/data.db `decision_log` before applying
      - If auto-apply enabled and guardrails pass: apply to market.db/pricing_list
        and publish price.update with actor="governance".
      - If not enabled or guardrails fail: log AWAITING_MANUAL_APPROVAL, no apply.
    """

    def __init__(self) -> None:
        self._callback = None

    async def start(self) -> None:
        async def on_proposal(pp: PriceProposal):
            try:
                self._handle_proposal_nonblocking(pp)
            except Exception as e:
                try:
                    print(f"[AutoApplier] on_proposal error: {e}")
                except Exception:
                    pass

        self._callback = on_proposal
        get_bus().subscribe(Topic.PRICE_PROPOSAL.value, self._callback)
        print("AutoApplier: subscribed to PRICE_PROPOSAL")

    async def stop(self) -> None:
        # Best-effort: _AsyncBus in agent_sdk doesn't have unsubscribe; ignore
        self._callback = None

    # --------------- internals ---------------
    def _settings_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "app" / "data.db"

    def _market_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "market.db"

    def _load_settings(self, conn: sqlite3.Connection) -> tuple[bool, float, float]:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        # Defaults
        defaults = {
            "auto_apply": "false",
            "min_margin": "0.12",
            "max_delta": "0.10",
        }
        # Ensure defaults exist if not set
        for k, v in defaults.items():
            cur.execute("SELECT value FROM settings WHERE key=?", (k,))
            if cur.fetchone() is None:
                cur.execute("INSERT INTO settings (key, value) VALUES (?,?)", (k, v))
        conn.commit()
        cur.execute("SELECT key, value FROM settings")
        kv = {k: (v or "") for k, v in cur.fetchall()}
        auto_apply = str(kv.get("auto_apply", defaults["auto_apply"])) .strip().lower() == "true"
        try:
            min_margin = float(kv.get("min_margin", defaults["min_margin"]))
        except Exception:
            min_margin = float(defaults["min_margin"])
        try:
            max_delta = float(kv.get("max_delta", defaults["max_delta"]))
        except Exception:
            max_delta = float(defaults["max_delta"])
        return auto_apply, min_margin, max_delta

    def _insert_decision(self,
                         sku: str,
                         old_price: Optional[float],
                         new_price: float,
                         margin: Optional[float],
                         algorithm: Optional[str],
                         decision: str,
                         actor: str,
                         proposal_id: Optional[str] = None) -> None:
        app_db_path = self._settings_path()
        try:
            conn = sqlite3.connect(app_db_path.as_posix(), check_same_thread=False)
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
                print(f"[AutoApplier] decision_log insert failed: {e}")
            except Exception:
                pass
        finally:
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass

    def _handle_proposal_nonblocking(self, pp: PriceProposal) -> None:
        # Evaluate guardrails quickly, then offload persistence/application work
        settings_db = self._settings_path().as_posix()
        try:
            conn = sqlite3.connect(settings_db, check_same_thread=False)
            auto_apply, min_margin, max_delta = self._load_settings(conn)
        except Exception as e:
            try:
                print(f"[AutoApplier] failed to load settings: {e}")
            except Exception:
                pass
            return
        finally:
            try:
                conn.close()
            except Exception:
                pass

        current_price = float(pp.current_price) if pp.current_price is not None else 0.0
        proposed_price = float(pp.proposed_price)
        if current_price > 0:
            delta_pct = abs(proposed_price - current_price) / current_price
        else:
            delta_pct = 0.0
        margin_ok = float(pp.margin) >= min_margin
        delta_ok = delta_pct <= max_delta

        # Always log a decision before potential application
        # Fetch old_price from market.pricing_list if available for more accurate logging
        old_price_for_log: Optional[float] = None
        try:
            mpath = self._market_path().as_posix()
            connm = sqlite3.connect(mpath, check_same_thread=False)
            curm = connm.cursor()
            curm.execute(
                "CREATE TABLE IF NOT EXISTS pricing_list (\n"
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                "  product_name TEXT NOT NULL,\n"
                "  optimized_price REAL NOT NULL,\n"
                "  last_update TEXT DEFAULT CURRENT_TIMESTAMP,\n"
                "  reason TEXT\n"
                ")"
            )
            curm.execute("SELECT optimized_price FROM pricing_list WHERE product_name=?", (pp.sku,))
            rmp = curm.fetchone()
            if rmp and rmp[0] is not None:
                old_price_for_log = float(rmp[0])
        except Exception:
            pass
        finally:
            try:
                connm.close()  # type: ignore[name-defined]
            except Exception:
                pass

        if not auto_apply or not (margin_ok and delta_ok):
            self._insert_decision(
                sku=pp.sku,
                old_price=old_price_for_log if old_price_for_log is not None else (pp.current_price if pp.current_price is not None else None),
                new_price=proposed_price,
                margin=float(pp.margin) if pp.margin is not None else None,
                algorithm=str(pp.algorithm) if pp.algorithm is not None else None,
                decision="AWAITING_MANUAL_APPROVAL",
                actor="governance",
                proposal_id=None,
            )
            return

        def _apply():
            app_db_path = self._settings_path()
            market_db_path = self._market_path()
            proposal_id: Optional[str] = None

            # Helper: find latest proposal_id for sku + proposed_price (if persisted by optimizer)
            try:
                c0 = sqlite3.connect(app_db_path.as_posix(), check_same_thread=False)
                cur0 = c0.cursor()
                cur0.execute(
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
                cur0.execute(
                    "SELECT id FROM price_proposals WHERE sku=? AND proposed_price=? ORDER BY ts DESC LIMIT 1",
                    (pp.sku, proposed_price),
                )
                r0 = cur0.fetchone()
                if r0:
                    proposal_id = r0[0]
            except Exception:
                pass
            finally:
                try:
                    c0.close()
                except Exception:
                    pass

            backoff = [0.01, 0.02, 0.05, 0.1, 0.25, 0.5]
            committed = False
            for i, delay in enumerate(backoff):
                conn = None
                try:
                    # Single connection; attach market DB for cross-db transaction
                    conn = sqlite3.connect(app_db_path.as_posix(), check_same_thread=False, isolation_level=None)
                    cur = conn.cursor()
                    esc = market_db_path.as_posix().replace("'", "''")
                    cur.execute(f"ATTACH DATABASE '{esc}' AS market")
                    # Ensure tables
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

                    # Compute old price for this transaction
                    cur.execute("SELECT optimized_price FROM market.pricing_list WHERE product_name=?", (pp.sku,))
                    row_old = cur.fetchone()
                    old_price = float(row_old[0]) if row_old and row_old[0] is not None else (float(pp.current_price) if pp.current_price is not None else None)

                    # Idempotency: if pricing_list already equals proposed_price, treat as success
                    if row_old and row_old[0] is not None:
                        try:
                            if float(row_old[0]) == proposed_price:
                                # Log decision (if we haven't already)
                                self._insert_decision(
                                    sku=pp.sku,
                                    old_price=old_price,
                                    new_price=proposed_price,
                                    margin=float(pp.margin) if pp.margin is not None else None,
                                    algorithm=str(pp.algorithm) if pp.algorithm is not None else None,
                                    decision="AUTO_APPLIED",
                                    actor="governance",
                                    proposal_id=proposal_id,
                                )
                                cur.execute("ROLLBACK")
                                committed = True
                                break
                        except Exception:
                            pass

                    # Insert decision_log BEFORE applying
                    try:
                        cur.execute(
                            "INSERT INTO decision_log (id, proposal_id, sku, old_price, new_price, margin, algorithm, decision, actor, ts)\n"
                            "VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (
                                str(uuid.uuid4()),
                                proposal_id,
                                pp.sku,
                                old_price,
                                proposed_price,
                                float(pp.margin) if pp.margin is not None else None,
                                str(pp.algorithm) if pp.algorithm is not None else None,
                                "AUTO_APPLIED",
                                "governance",
                                _utc_now_iso(),
                            ),
                        )
                    except Exception:
                        # decision logging best-effort inside txn; continue
                        pass

                    # Upsert pricing_list in attached DB
                    cur.execute(
                        "SELECT 1 FROM market.pricing_list WHERE product_name=?",
                        (pp.sku,),
                    )
                    exists_m = cur.fetchone() is not None
                    if exists_m:
                        cur.execute(
                            "UPDATE market.pricing_list SET optimized_price=?, last_update=CURRENT_TIMESTAMP, reason=? WHERE product_name=?",
                            (proposed_price, "auto_applied(governance)", pp.sku),
                        )
                    else:
                        cur.execute(
                            "INSERT INTO market.pricing_list (product_name, optimized_price, last_update, reason) VALUES (?,?,CURRENT_TIMESTAMP,?)",
                            (pp.sku, proposed_price, "auto_applied(governance)"),
                        )

                    cur.execute("COMMIT")
                    committed = True
                    break
                except sqlite3.OperationalError as e:
                    try:
                        cur.execute("ROLLBACK")
                    except Exception:
                        pass
                    if "locked" in str(e).lower() or "busy" in str(e).lower():
                        time.sleep(delay)
                        continue
                    else:
                        try:
                            print(f"[AutoApplier] OperationalError: {e}")
                        except Exception:
                            pass
                        break
                except Exception as e:
                    try:
                        cur.execute("ROLLBACK")
                    except Exception:
                        pass
                    try:
                        print(f"[AutoApplier] apply error: {e}")
                    except Exception:
                        pass
                    break
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass

            if not committed:
                return

            # Publish schema-compliant price.update event after commit
            payload = {
                "proposal_id": proposal_id or str(uuid.uuid4()),
                "product_id": pp.sku,
                "final_price": proposed_price,
            }

            async def _pub():
                try:
                    await get_bus().publish(Topic.PRICE_UPDATE.value, payload)
                except Exception as e:
                    try:
                        print(f"[AutoApplier] publish PRICE_UPDATE failed: {e}")
                    except Exception:
                        pass

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_pub())
            except RuntimeError:
                threading.Thread(target=lambda: asyncio.run(_pub()), daemon=True).start()

        # Offload to background thread to avoid blocking the bus callback
        threading.Thread(target=_apply, daemon=True).start()
