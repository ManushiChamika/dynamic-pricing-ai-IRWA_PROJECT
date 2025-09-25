import asyncio
import threading
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any, Optional, Coroutine

# Central background event loop for UI async calls


class _LoopHolder:
    loop: Optional[asyncio.AbstractEventLoop] = None
    thread: Optional[threading.Thread] = None


_holder = _LoopHolder()


def ensure_bg_loop() -> asyncio.AbstractEventLoop:
    if _holder.loop and _holder.loop.is_running():
        return _holder.loop
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=loop.run_forever, daemon=True)
    t.start()
    _holder.loop = loop
    _holder.thread = t
    return loop


def run_async(coro: Coroutine[Any, Any, Any], timeout: float | None = 10.0) -> Any:
    """Run a coroutine on the background loop and wait for a result.

    Note: Accepts coroutine objects (not plain Awaitables) to satisfy type checkers
    and runtime expectations of run_coroutine_threadsafe.
    """
    loop = ensure_bg_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        return fut.result(timeout=timeout)
    except FuturesTimeout:
        return None
    except Exception:
        return None
