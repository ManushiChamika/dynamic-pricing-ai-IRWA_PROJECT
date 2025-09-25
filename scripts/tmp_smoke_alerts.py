import asyncio
from types import SimpleNamespace
from core.agents.alert_service import api as alerts
from core.agents.agent_sdk import get_bus, Topic

async def main():
    await alerts.start()
    spec = {
        "id": "rule_ui_smoke",
        "source": "MARKET_TICK",
        "where": "competitor_price < our_price and demand_index > 0.8",
        "detector": None,
        "field": None,
        "params": {},
        "hold_for": None,
        "severity": "warn",
        "dedupe": "sku",
        "group_by": [],
        "notify": {"channels": ["ui"], "throttle": None, "webhook_url": None, "email_to": None},
        "enabled": True,
    }
    print("creating rule...")
    print(await alerts.create_rule(spec))
    bus = get_bus()
    tick = SimpleNamespace(sku="SKU-123", market="DEFAULT", our_price=100.0, competitor_price=90.0, demand_index=0.9)
    print("publishing tick...")
    await bus.publish(Topic.MARKET_TICK.value, tick)
    incs = await alerts.list_incidents("OPEN")
    print("incidents:", incs)

if __name__ == "__main__":
    asyncio.run(main())
