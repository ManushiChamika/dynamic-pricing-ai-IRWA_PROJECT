from __future__ import annotations

import asyncio
from pathlib import Path as _Path0
import sys as _Sys0

# Ensure repo root on sys.path for module imports
_root0 = _Path0(__file__).resolve().parents[1]
if str(_root0) not in _Sys0.path:
    _Sys0.path.insert(0, str(_root0))

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




