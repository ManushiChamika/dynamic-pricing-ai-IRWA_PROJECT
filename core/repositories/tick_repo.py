# core/repositories/tick_repo.py
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select

from core.db import SessionLocal
from core.models import MarketTick


class TickRepo:
    """Lightweight repository for reading/writing market ticks with async-friendly APIs."""

    def __init__(self, session_factory=SessionLocal):
        self.SessionLocal = session_factory

    async def insert_tick(
        self,
        *,
        symbol: str,
        price: float,
        source: str = "mock",
        timestamp: Optional[datetime] = None,
    ) -> MarketTick:
        """
        Insert a tick row. Runs blocking DB work in a worker thread so it can be awaited.
        """
        def _work() -> MarketTick:
            ts = timestamp or datetime.now(timezone.utc)
            with self.SessionLocal() as db:
                row = MarketTick(symbol=symbol, price=price, source=source, timestamp=ts)
                db.add(row)
                db.commit()
                db.refresh(row)
                return row

        return await asyncio.to_thread(_work)

    async def latest_ticks(self, limit: int = 50) -> List[MarketTick]:
        """
        Fetch latest ticks ordered by timestamp desc. Also runs in a thread.
        """
        def _work() -> List[MarketTick]:
            with self.SessionLocal() as db:
                stmt = (
                    select(MarketTick)
                    .order_by(MarketTick.timestamp.desc())
                    .limit(limit)
                )
                return list(db.execute(stmt).scalars().all())

        return await asyncio.to_thread(_work)
