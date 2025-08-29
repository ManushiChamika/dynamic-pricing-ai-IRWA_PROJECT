# --- path bootstrap ---
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in [HERE, *HERE.parents] if (p / "core").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ----------------------

import streamlit as st
import sqlite3
import uuid
from datetime import datetime, timezone
import asyncio
import threading

from core.bus import bus as _bus
from core.protocol import Topic


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


st.set_page_config(page_title="Proposals & Approvals", page_icon="✅", layout="wide")
st.title("Proposals & Approvals")
st.write("Accept applies price to pricing_list and publishes PRICE_UPDATE.")


def _open_app_db():
    db_path = (ROOT / "app" / "data.db").as_posix()
    return sqlite3.connect(db_path, check_same_thread=False)


def _open_market_db():
    db_path = (ROOT / "market.db").as_posix()
    return sqlite3.connect(db_path, check_same_thread=False)


def _ensure_tables(conn_app: sqlite3.Connection) -> None:
    cur = conn_app.cursor()
    # actions audit table (additive)
    cur.execute(
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
    # proposals table should exist; keep page robust if missing
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
    conn_app.commit()


def _load_proposals_with_status(conn_app: sqlite3.Connection):
    cur = conn_app.cursor()
    cur.execute(
        "SELECT id, sku, proposed_price, current_price, margin, algorithm, ts\n"
        "FROM price_proposals ORDER BY ts ASC"
    )
    rows = cur.fetchall()
    proposals = []
    for pid, sku, p_price, c_price, margin, algo, ts in rows:
        cur.execute(
            "SELECT action, actor, ts FROM proposal_actions WHERE proposal_id=?\n"
            "ORDER BY ts DESC LIMIT 1",
            (pid,),
        )
        act = cur.fetchone()
        status = {
            "state": "PENDING",
            "actor": None,
            "ts": None,
        }
        if act:
            status = {"state": act[0], "actor": act[1], "ts": act[2]}
        proposals.append(
            {
                "proposal_id": pid,
                "sku": sku,
                "proposed_price": p_price,
                "current_price": c_price,
                "margin": margin,
                "algorithm": algo,
                "ts": ts,
                "status": status,
            }
        )
    return proposals


def _apply_price_async(sku: str, proposed_price: float, proposal_id: str) -> None:
    # Write to market.db.pricing_list (upsert) and publish PRICE_UPDATE
    def _work():
        try:
            conn = _open_market_db()
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
            # upsert by product_name
            cur.execute(
                "SELECT product_name FROM pricing_list WHERE product_name=?",
                (sku,),
            )
            exists = cur.fetchone() is not None
            if exists:
                cur.execute(
                    "UPDATE pricing_list SET optimized_price=?, last_update=CURRENT_TIMESTAMP, reason=? WHERE product_name=?",
                    (float(proposed_price), "accepted_via_ui", sku),
                )
            else:
                cur.execute(
                    "INSERT INTO pricing_list (product_name, optimized_price, last_update, reason)\n"
                    "VALUES (?,?,CURRENT_TIMESTAMP,?)",
                    (sku, float(proposed_price), "accepted_via_ui"),
                )
            conn.commit()
        except Exception as e:
            try:
                print(f"[6_Proposals] pricing_list upsert failed: {e}")
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

        payload = {
            "sku": sku,
            "new_price": float(proposed_price),
            "actor": "local",
            "proposal_id": proposal_id,
        }

        async def _publish():
            try:
                await _bus.publish(Topic.PRICE_UPDATE.value, payload)
            except Exception as e:
                try:
                    print(f"[6_Proposals] publish PRICE_UPDATE failed: {e}")
                except Exception:
                    pass

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_publish())
        except RuntimeError:
            threading.Thread(target=lambda: asyncio.run(_publish()), daemon=True).start()

    threading.Thread(target=_work, daemon=True).start()


def _render():
    conn = _open_app_db()
    _ensure_tables(conn)
    proposals = _load_proposals_with_status(conn)

    st.subheader("Pending & historical proposals")

    if not proposals:
        st.info("No proposals found.")
        return

    for p in proposals:
        cols = st.columns([2,2,2,2,2,2,3])
        cols[0].markdown(f"**SKU**: {p['sku']}")
        cols[1].markdown(f"**Proposed**: {p['proposed_price']}")
        cols[2].markdown(f"**Current**: {p['current_price']}")
        cols[3].markdown(f"**Margin**: {p['margin']:.2%}" if isinstance(p['margin'], (int,float)) else f"**Margin**: {p['margin']}")
        cols[4].markdown(f"**Algo**: {p['algorithm']}")
        st_state = p["status"]["state"]
        cols[5].markdown(f"**Status**: {st_state}")

        if st_state == "PENDING":
            accept_key = f"accept_{p['proposal_id']}"
            reject_key = f"reject_{p['proposal_id']}"
            if cols[6].button("Accept", key=accept_key):
                try:
                    # insert action
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO proposal_actions (id, proposal_id, action, actor, ts) VALUES (?,?,?,?,?)",
                        (str(uuid.uuid4()), p["proposal_id"], "ACCEPTED", "local", _utc_now_iso()),
                    )
                    conn.commit()
                except Exception as e:
                    st.error(f"Failed to insert proposal action: {e}")
                else:
                    _apply_price_async(p["sku"], p["proposed_price"], p["proposal_id"])
                    st.success("Accepted. Applying price and publishing event...")
                    st.experimental_rerun()
            if cols[6].button("Reject", key=reject_key):
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO proposal_actions (id, proposal_id, action, actor, ts) VALUES (?,?,?,?,?)",
                        (str(uuid.uuid4()), p["proposal_id"], "REJECTED", "local", _utc_now_iso()),
                    )
                    conn.commit()
                except Exception as e:
                    st.error(f"Failed to insert proposal action: {e}")
                else:
                    st.info("Rejected.")
                    st.experimental_rerun()
        else:
            cols[6].markdown(f"by {p['status'].get('actor') or '-'} at {p['status'].get('ts') or '-'}")

    try:
        conn.close()
    except Exception:
        pass


_render()


