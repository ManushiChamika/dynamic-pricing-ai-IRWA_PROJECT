# --- path bootstrap ---
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in [HERE, *HERE.parents] if (p / "core").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ----------------------

import streamlit as st
import sqlite3
from datetime import datetime, timezone
import threading
import asyncio

from core.agents.data_collector import mcp_server as svc


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _open_app_db() -> sqlite3.Connection:
    return sqlite3.connect((ROOT / "app" / "data.db").as_posix(), check_same_thread=False)


def _ensure_ingestion_jobs(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_jobs (
          id TEXT PRIMARY KEY,
          sku TEXT,
          market TEXT,
          connector TEXT,
          depth INTEGER,
          status TEXT,
          error TEXT,
          created_at TEXT,
          started_at TEXT,
          finished_at TEXT
        )
        """
    )
    conn.commit()


def _read_jobs(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(
        "SELECT id, sku, market, connector, depth, status, created_at, started_at, finished_at, error\n"
        "FROM ingestion_jobs ORDER BY COALESCE(created_at, '') DESC"
    )
    rows = cur.fetchall()
    jobs = []
    for r in rows:
        jobs.append(
            {
                "id": r[0],
                "sku": r[1],
                "market": r[2],
                "connector": r[3],
                "depth": r[4],
                "status": r[5],
                "created_at": r[6],
                "started_at": r[7],
                "finished_at": r[8],
                "error": r[9],
            }
        )
    return jobs


def _update_job_status(conn: sqlite3.Connection, job_id: str, status: str, error: str | None = None) -> None:
    cur = conn.cursor()
    if status in {"CANCELLED", "FAILED", "DONE"}:
        cur.execute(
            "UPDATE ingestion_jobs SET status=?, error=?, finished_at=? WHERE id=?",
            (status, error, _utc_now_iso(), job_id),
        )
    else:
        cur.execute(
            "UPDATE ingestion_jobs SET status=?, error=? WHERE id=?",
            (status, error, job_id),
        )
    conn.commit()


st.set_page_config(page_title="Ingestion Jobs", page_icon="🧰", layout="wide")
st.title("Ingestion Jobs")

if st.button("Refresh"):
    st.experimental_rerun()

with st.expander("Start new job", expanded=True):
    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
    sku = c1.text_input("SKU", value="SKU-123")
    market = c2.text_input("Market", value="DEFAULT")
    connector = c3.selectbox("Connector", options=["mock"], index=0)
    depth = int(c4.number_input("Depth", min_value=1, max_value=50, value=3, step=1))
    start_btn = c5.button("Start Job")

    if start_btn:
        def _start_job_bg():
            try:
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                async def _run():
                    try:
                        res = await svc.start_collection(sku, market=market, connector=connector, depth=depth)
                        print("start_collection:", res)
                    except Exception as e:
                        print("start_collection failed:", e)
                if loop:
                    loop.create_task(_run())
                else:
                    asyncio.run(_run())
            finally:
                # trigger UI refresh on completion
                st.experimental_rerun()
        threading.Thread(target=_start_job_bg, daemon=True).start()
        st.info("Starting job...")

conn = _open_app_db()
_ensure_ingestion_jobs(conn)
jobs = _read_jobs(conn)

st.subheader("Jobs")
if not jobs:
    st.info("No jobs found.")
else:
    for j in jobs:
        cols = st.columns([3, 2, 2, 2, 1.5, 2, 2, 2, 3])
        cols[0].markdown(f"**job_id**: `{j['id']}`")
        cols[1].markdown(f"**sku**: {j['sku']}")
        cols[2].markdown(f"**market**: {j['market']}")
        cols[3].markdown(f"**connector**: {j['connector']}")
        cols[4].markdown(f"**depth**: {j['depth']}")
        cols[5].markdown(f"**status**: {j['status']}")
        cols[6].markdown(f"**started**: {j['started_at'] or '-'}")
        cols[7].markdown(f"**finished**: {j['finished_at'] or '-'}")
        cols[8].markdown(f"**error**: {j['error'] or '-'}")

        if j["status"] in {"QUEUED", "RUNNING"}:
            cA, cB = st.columns([1, 1])
            if cA.button("Cancel", key=f"cancel_{j['id']}"):
                try:
                    _update_job_status(conn, j["id"], "CANCELLED", error="cancelled")
                    st.success("Cancelled job.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Cancel failed: {e}")
            if cB.button("Mark Failed", key=f"fail_{j['id']}"):
                try:
                    _update_job_status(conn, j["id"], "FAILED", error="manually_marked")
                    st.warning("Marked job as FAILED.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Mark failed: {e}")

try:
    conn.close()
except Exception:
    pass




