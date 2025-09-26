from __future__ import annotations

import asyncio

from core.agents.auto_applier import AutoApplier


async def main() -> None:
    aa = AutoApplier()
    await aa.start()
    print("AutoApplier started. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        await aa.stop()


if __name__ == "__main__":
    asyncio.run(main())



