from __future__ import annotations

import asyncio
import threading
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import uuid
from typing import Optional

from core.bus import bus
from core.protocol import Topic
from core.models import PriceProposal
from core.agents.data_collector.repo import DataRepo


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutoApplier:
    """Subscribe to PRICE_PROPOSAL and auto-apply per merchant guardrails.

    Guardrails are stored in app/data.db settings table with keys:
      - auto_apply: 'true' | 'false'
      - min_margin: float as string
      - max_delta: float as string (relative allowed change vs current_price)
    """

    def __init__(self, repo: Optional[DataRepo] = None) -> None:
        self.repo = repo or DataRepo()
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
        bus.subscribe(Topic.PRICE_PROPOSAL.value, self._callback)
        print("AutoApplier: subscribed to PRICE_PROPOSAL")

    async def stop(self) -> None:
        if self._callback:
            try:
                bus.unsubscribe(Topic.PRICE_PROPOSAL.value, self._callback)
            except Exception:
                pass
            self._callback = None

    # --------------- internals ---------------
    def _settings_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "app" / "data.db"

    def _market_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "market.db"

    def _load_settings(self, conn: sqlite3.Connection) -> tuple[bool, float, float]:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"
        )
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

        if not auto_apply or not (margin_ok and delta_ok):
            return

        def _apply():
            app_db = self._settings_path().as_posix()
            market_db = self._market_path().as_posix()
            proposal_id: Optional[str] = None
            try:
                c = sqlite3.connect(app_db, check_same_thread=False)
                cu = c.cursor()
                # Ensure tables exist
                cu.execute(
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
                cu.execute(
                    """
                    CREATE TABLE IF NOT EXISTS proposal_actions (
                      id TEXT PRIMARY KEY,
                      proposal_id TEXT,
                      action TEXT,
                      actor TEXT,
                      ts TEXT
                    )
                    """
                )
                # Find proposal_id by sku + proposed_price (most recent)
                cu.execute(
                    "SELECT id FROM price_proposals WHERE sku=? AND proposed_price=? ORDER BY ts DESC LIMIT 1",
                    (pp.sku, proposed_price),
                )
                r = cu.fetchone()
                if r:
                    proposal_id = r[0]
                # Insert action row
                cu.execute(
                    "INSERT INTO proposal_actions (id, proposal_id, action, actor, ts) VALUES (?,?,?,?,?)",
                    (str(uuid.uuid4()), proposal_id, "AUTO_APPLIED", "auto", _utc_now_iso()),
                )
                c.commit()
            except Exception as e:
                try:
                    print(f"[AutoApplier] record AUTO_APPLIED failed: {e}")
                except Exception:
                    pass
            finally:
                try:
                    c.close()
                except Exception:
                    pass

            # Upsert market pricing_list
            try:
                cm = sqlite3.connect(market_db, check_same_thread=False)
                um = cm.cursor()
                um.execute(
                    "CREATE TABLE IF NOT EXISTS pricing_list (\n"
                    "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                    "  product_name TEXT NOT NULL,\n"
                    "  optimized_price REAL NOT NULL,\n"
                    "  last_update TEXT DEFAULT CURRENT_TIMESTAMP,\n"
                    "  reason TEXT\n"
                    ")"
                )
                um.execute(
                    "SELECT product_name FROM pricing_list WHERE product_name=?",
                    (pp.sku,),
                )
                exists = um.fetchone() is not None
                if exists:
                    um.execute(
                        "UPDATE pricing_list SET optimized_price=?, last_update=CURRENT_TIMESTAMP, reason=? WHERE product_name=?",
                        (proposed_price, "auto_applied", pp.sku),
                    )
                else:
                    um.execute(
                        "INSERT INTO pricing_list (product_name, optimized_price, last_update, reason) VALUES (?,?,CURRENT_TIMESTAMP,?)",
                        (pp.sku, proposed_price, "auto_applied"),
                    )
                cm.commit()
            except Exception as e:
                try:
                    print(f"[AutoApplier] pricing_list upsert failed: {e}")
                except Exception:
                    pass
            finally:
                try:
                    cm.close()
                except Exception:
                    pass

            # Publish PRICE_UPDATE event
            payload = {
                "sku": pp.sku,
                "new_price": proposed_price,
                "actor": "auto",
                "proposal_id": proposal_id,
                "action": "AUTO_APPLY",
            }

            async def _pub():
                try:
                    await bus.publish(Topic.PRICE_UPDATE.value, payload)
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


