from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import sys

from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.collector import DataCollector
from core.agents.data_collector.connectors.mock import mock_ticks


async def main():
    repo = DataRepo()  # uses DATA_DB or app/data.db
    await repo.init()
    dc = DataCollector(repo)

    # Ingest a few mock ticks
    await dc.ingest_stream(mock_ticks(n=3), delay_s=0.1)

    # Fetch features for the last day
    since_iso = (datetime.now(timezone.utc)).isoformat()
    # We inserted just now, so features_for with wide window:
    res = await repo.features_for("SKU-123", "DEFAULT", "1970-01-01T00:00:00+00:00")
    print("FEATURES:", res)
    ok = bool(res.get("count", 0) > 0)
    if ok:
        print("SMOKE PASS: features count > 0")
    else:
        print("SMOKE FAIL: features count == 0")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())


