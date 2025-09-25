from __future__ import annotations

import asyncio
import sys, pathlib
from datetime import datetime, timezone
from types import SimpleNamespace

# Ensure repository root on sys.path
HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.agents.alert_service import api as alerts
from core.agents.agent_sdk import get_bus, Topic


async def main() -> int:
    # Start alert engine
    await alerts.start()

    # Ensure at least one rule exists for PRICE_PROPOSAL
    rules = await alerts.list_rules()
    if not any(r.get("source") == "PRICE_PROPOSAL" for r in rules):
        spec = {
            "id": "pp_margin_low",
            "source": "PRICE_PROPOSAL",
            "where": "margin < 0.3",
            "detector": None,
            "field": None,
            "params": {},
            "hold_for": None,
            "severity": "warn",
            "dedupe": "sku",
            "group_by": [],
            "notify": {"channels": ["ui"], "throttle": "5s"},
            "enabled": True,
        }
        cr = await alerts.create_rule(spec)
        print("create_rule:", cr)

    # Publish a price proposal that should trigger the rule
    bus = get_bus()
    pp = SimpleNamespace(
        sku="SKU-PP",
        proposed_price=95.0,
        margin=0.25,
        ts=datetime.now(timezone.utc),
    )
    await bus.publish(Topic.PRICE_PROPOSAL.value, pp)

    # Give engine time to correlate and deliver
    await asyncio.sleep(0.5)

    # Verify incident exists
    incidents = await alerts.list_incidents(None)
    got = [i for i in incidents if i.get("rule_id") == "pp_margin_low" and i.get("sku") == "SKU-PP"]
    ok = len(got) >= 1
    print("incidents count:", len(incidents))
    print("matching incidents:", len(got))
    print("SMOKE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
