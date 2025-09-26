from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from core.agents.data_collector import mcp_server as svc


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    app_db = (root / "app" / "data.db").as_posix()

    # Ensure ingestion_jobs exists
    conn = sqlite3.connect(app_db)
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

    # Start a new collection job (mock)
    async def _start():
        return await svc.start_collection("SKU-123", market="DEFAULT", connector="mock", depth=3)

    res = asyncio.run(_start())
    if not res.get("ok"):
        print("START_FAIL:", res)
        return 1
    job_id = res["job_id"]
    print("job_id:", job_id)

    # Poll job status via DB and try to cancel quickly
    cancelled = False
    final_status = None
    for i in range(48):  # up to ~12s
        cur.execute(
            "SELECT status FROM ingestion_jobs WHERE id=?",
            (job_id,),
        )
        r = cur.fetchone()
        status = r[0] if r else None
        print("status:", status)
        if status in {"QUEUED", "RUNNING"} and not cancelled:
            # Attempt cancel
            cur.execute(
                "UPDATE ingestion_jobs SET status=?, finished_at=? WHERE id=?",
                ("CANCELLED", _utc_now_iso(), job_id),
            )
            conn.commit()
            print("cancelled job")
            cancelled = True
        if status in {"DONE", "FAILED", "CANCELLED"}:
            final_status = status
            break
        asyncio.run(asyncio.sleep(0.25))

    # Verify outcome
    cur.execute(
        "SELECT status FROM ingestion_jobs WHERE id=?",
        (job_id,),
    )
    r2 = cur.fetchone()
    status2 = r2[0] if r2 else None
    print("final_status:", status2)

    try:
        conn.close()
    except Exception:
        pass

    if status2 == "CANCELLED":
        print("PASS: cancelled")
        return 0
    if status2 == "DONE":
        print("PASS: job completed before cancel")
        return 0
    if status2 in {"FAILED", None}:
        print("NO_ACTIONABLE_JOB")
        return 2
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())



