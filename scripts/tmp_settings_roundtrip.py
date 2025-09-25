import asyncio
from core.agents.alert_service import api as alerts

async def main():
    await alerts.start()
    s = await alerts.get_settings()
    print("defaults:", s)
    new = dict(s)
    new["email_to"] = ["qa@example.com"]
    ok = await alerts.save_settings(new)
    print("saved:", ok)
    s2 = await alerts.get_settings()
    print("after:", s2)

if __name__ == "__main__":
    asyncio.run(main())
