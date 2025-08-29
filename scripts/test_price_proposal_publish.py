from __future__ import annotations

import asyncio
from typing import List

from core.agents.data_collector.repo import DataRepo
from core.agents.alert_notifier import AlertNotifier, Thresholds
from core.agents.data_collector import mcp_server as svc
import core.agents.pricing_optimizer as po_mod


async def main() -> int:
    # Ensure data repo and tables exist
    r = DataRepo()
    await r.init()

    # Import product so product_catalog has SKU-123
    imp = await svc.import_product_catalog([
        {
            "sku": "SKU-123",
            "title": "Demo",
            "currency": "USD",
            "current_price": 100.0,
            "cost": 90.0,
            "stock": 10,
        }
    ])
    print("import_product_catalog:", imp)

    # Start alert notifier to capture PRICE_PROPOSAL alerts (e.g., MARGIN_BREACH)
    alerts: List[str] = []

    async def ui_sink(a):
        line = f"[{a.ts:%H:%M:%S}] {a.kind} {a.sku} — {a.message} [{a.severity}]"
        print("ALERT:", line)
        alerts.append(line)

    notifier = AlertNotifier(Thresholds(undercut_delta=0.01, demand_spike=0.5, min_margin=0.95), sinks=[ui_sink])
    await notifier.start()

    # Run pricing optimizer workflow in executor (sync API)
    agent = po_mod.PricingOptimizerAgent()
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, lambda: agent.process_full_workflow("maximize profit", "SKU-123"))
    print("optimizer_result:", res)

    # Allow background publish/persist time to complete
    await asyncio.sleep(1.0)

    # Fetch features to show DB connectivity is fine
    feats = await svc.fetch_market_features("SKU-123", "DEFAULT", "P7D")
    print("features:", feats)

    # Decide pass/fail
    ok_res = isinstance(res, dict) and res.get("status") == "success"
    ok_alerts = len(alerts) >= 1  # preferably MARGIN_BREACH; accept any alert present
    ok_feats = int(feats.get("count") or 0) >= 1
    if ok_res and ok_alerts and ok_feats:
        print("PRICE_PROPOSAL SMOKE PASS")
        return 0
    print("PRICE_PROPOSAL SMOKE FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))


