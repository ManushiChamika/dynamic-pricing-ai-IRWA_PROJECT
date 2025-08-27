# core/util/retry.py
import asyncio, random
from typing import Awaitable, Callable, Tuple, Type

async def retry(
    fn: Callable[[], Awaitable[None]],
    attempts: int = 3,
    base: float = 0.4,
    cap: float = 3.0,
    retry_on: Tuple[Type[BaseException], ...] = (Exception,),
) -> None:
    delay = base
    for i in range(attempts):
        try:
            return await fn()
        except retry_on:
            if i == attempts - 1:
                raise
            await asyncio.sleep(delay)
            # exponential backoff with small jitter
            delay = min(cap, delay * (2 + random.random() * 0.2))
