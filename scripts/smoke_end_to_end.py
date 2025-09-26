# scripts/smoke_end_to_end.py
from __future__ import annotations

import asyncio
from typing import List

from core.agents.data_collector import mcp_server as svc
from core.agents.alert_notifier import AlertNotifier, Thresholds


async def smoke() -> int:
    alerts: List[str] = []

    async def ui_sink(a):
        line = f"[{a.ts:%H:%M:%S}] {a.kind} {a.sku} — {a.message} [{a.severity}]"
        print("ALERT:", line)
        alerts.append(line)

    # 1) Ensure DB
    await svc._repo.init()

    # 2) Import product
    imp = await svc.import_product_catalog([
        {
            "sku": "SKU-123",
            "title": "Demo",
            "currency": "USD",
            "current_price": 100.0,
            "cost": 80.0,
            "stock": 10,
        }
    ])
    print("import_product_catalog:", imp)
    if not imp.get("ok"):
        print("FAIL: import_product_catalog returned error")
        return 1

    # 3) Start notifier before ingestion so we capture alerts
    t = Thresholds(undercut_delta=0.01, demand_spike=0.5, min_margin=0.10)
    notifier = AlertNotifier(t, sinks=[ui_sink])
    await notifier.start()

    # 4) Start collection job
    start = await svc.start_collection("SKU-123", market="DEFAULT", connector="mock", depth=5)
    if not start.get("ok"):
        print("FAIL: start_collection returned error:", start)
        return 1
    job_id = start["job_id"]
    print("job_id:", job_id)

    # 5) Poll job status up to 12s
    final_status = None
    for _ in range(48):  # 48 * 0.25s = 12s
        st = await svc.get_job_status(job_id)
        print("job_status:", st)
        if st.get("ok"):
            s = st.get("job", {}).get("status")
            if s in {"DONE", "FAILED"}:
                final_status = s
                break
        await asyncio.sleep(0.25)

    # 6) Fetch features
    feats = await svc.fetch_market_features("SKU-123", "DEFAULT", "P7D")
    print("features:", feats)

    # 7) Summarize & decide pass/fail
    count = int(feats.get("count") or 0)
    print("summary:")
    print("  final_status:", final_status)
    print("  alerts_collected:", len(alerts))
    for ln in alerts[:5]:
        print("  ", ln)

    passed = (
        final_status == "DONE" and count >= 1 and len(alerts) >= 1
    )
    if passed:
        print("E2E SMOKE PASS")
        return 0
    else:
        print("E2E SMOKE FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(smoke()))

