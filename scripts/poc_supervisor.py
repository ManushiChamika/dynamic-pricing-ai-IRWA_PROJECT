from __future__ import annotations

import asyncio
import csv
import sys
from pathlib import Path
from typing import List, Dict

from core.agents.supervisor import Supervisor


def _load_rows_from_csv(path: str) -> List[Dict]:
    rows: List[Dict] = []
    with open(path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            # normalize
            r["sku"] = (r.get("sku") or "").strip()
            if not r["sku"]:
                continue
            rows.append(r)
    return rows


async def main(argv: List[str]) -> int:
    if len(argv) > 1:
        src = argv[1]
        rows = _load_rows_from_csv(src)
    else:
        rows = [
            {"sku": "SKU-123", "title": "Demo", "currency": "USD", "current_price": 100.0, "cost": 80.0, "stock": 10, "market": "DEFAULT", "connector": "mock", "depth": 3}
        ]

    sup = Supervisor(concurrency=2)
    summary = await sup.run_for_catalog(rows, apply_auto=False)
    print("SUMMARY:", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv)))



