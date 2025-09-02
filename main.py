import asyncio
from core.db import init_db
from core.message_bus import MessageBus
from core.agents.data_collector.collector import DataCollector
from core.agents.optimizer.optimizer import Optimizer
from core.agents.auto_applier.auto_applier import AutoApplier

async def main():
    init_db()
    bus = MessageBus()

    collector = DataCollector(bus)
    optimizer = Optimizer(bus)
    applier = AutoApplier(bus)

    # run agents
    tasks = [
        asyncio.create_task(optimizer.run()),
        asyncio.create_task(applier.run()),
        # demo poller (replace with your real feed)
        asyncio.create_task(collector.poll_external_feed_forever(interval_sec=15)),
    ]

    # demo: also push one manual tick at startup
    await collector.ingest_tick({
        "sku": "DEMO-1",
        "our_price": 50.0,
        "competitor_price": 49.5,
        "demand_index": 0.7,
    })

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
