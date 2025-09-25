import asyncio
from core.agents.alert_service import api as alerts

async def main():
    await alerts.start()
    incs = await alerts.list_incidents("OPEN")
    print("open:", incs)
    if not incs:
        return
    inc_id = incs[0]["id"]
    print("acking", inc_id)
    print(await alerts.ack_incident(inc_id))
    print("resolving", inc_id)
    print(await alerts.resolve_incident(inc_id))

if __name__ == "__main__":
    asyncio.run(main())
