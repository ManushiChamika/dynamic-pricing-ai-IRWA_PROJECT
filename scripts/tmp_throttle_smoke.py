import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from core.agents.alert_service import api as alerts
from core.agents.agent_sdk import get_bus, Topic


async def main():
    await alerts.start()
    bus = get_bus()

    rule_id = "rule_throttle_smoke"
    spec = {
        "id": rule_id,
        "source": "MARKET_TICK",
        "where": "competitor_price < our_price",
        "detector": None,
        "field": None,
        "params": {},
        "hold_for": None,
        "severity": "info",
        "dedupe": "sku",
        "group_by": [],
        "notify": {"channels": ["ui"], "throttle": "15m", "webhook_url": None, "email_to": None},
        "enabled": True,
    }

    print("creating/upserting rule...", await alerts.create_rule(spec))

    tick = SimpleNamespace(
        sku="SKU-T1",
        market="DEFAULT",
        our_price=100.0,
        competitor_price=90.0,
        demand_index=0.5,
        ts=datetime.now(timezone.utc),
    )

    print("publishing first tick (should create incident)...")
    await bus.publish(Topic.MARKET_TICK.value, tick)
    incs1 = await alerts.list_incidents("OPEN")
    print("open after first:", incs1)

    print("publishing second tick quickly (should throttle, no new incident)...")
    tick.ts = datetime.now(timezone.utc)
    await bus.publish(Topic.MARKET_TICK.value, tick)
    incs2 = await alerts.list_incidents("OPEN")
    print("open after second:", incs2)

    same_ids = {r["id"] for r in incs1} == {r["id"] for r in incs2}
    print("incident ids unchanged:", same_ids)

    # Check last_seen increased for the throttled incident
    if incs2:
        before = {r["id"]: r["last_seen"] for r in incs1}
        after = {r["id"]: r["last_seen"] for r in incs2}
        any_updated = False
        for iid in after:
            if iid in before and after[iid] > before[iid]:
                any_updated = True
                print(f"last_seen updated for {iid}: {before[iid]} -> {after[iid]}")
        print("last_seen updated (via touch_incident):", any_updated)


if __name__ == "__main__":
    asyncio.run(main())
