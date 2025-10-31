from __future__ import annotations

from typing import Any, Dict, List, Callable, Optional
import json
from datetime import datetime
import contextvars

try:
    from .user_interact.context import get_owner_id as _get_owner_id  # type: ignore
except Exception:
    def _get_owner_id() -> Optional[str]:  # fallback if user_interact is unavailable
        return None


class ChatExecutor:
    def __init__(self, log):
        self._log = log

    def execute_tool_call(
        self,
        fn_name: Optional[str],
        raw_args: str,
        functions_map: Dict[str, Callable[..., Any]],
        tools_used: List[str],
        trace_id: Optional[str] = None,
    ) -> Any:
        try:
            if fn_name and fn_name not in tools_used:
                tools_used.append(fn_name)
        except Exception:
            pass

        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
        except Exception:
            args = {}

        tool_start_time = datetime.now()
        result: Any
        error_occurred = False

        if fn_name in functions_map:
            try:
                try:
                    owner = _get_owner_id()
                    self._log.debug(f"Tool call starting: {fn_name} owner_id={owner}")
                except Exception:
                    pass

                result = functions_map[fn_name](**args)
            except TypeError:
                result = functions_map[fn_name](args)
            except Exception as tool_exc:
                result = {"error": str(tool_exc)}
                error_occurred = True

            if hasattr(result, '__await__'):
                import asyncio
                from concurrent.futures import ThreadPoolExecutor

                ctx = contextvars.copy_context()

                def run_in_new_loop():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(result)  # type: ignore[arg-type]
                    finally:
                        new_loop.close()

                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(ctx.run, run_in_new_loop)
                    result = future.result()
        else:
            result = {"error": f"unknown tool: {fn_name}"}
            error_occurred = True

        try:
            if trace_id:
                duration_ms = int((datetime.now() - tool_start_time).total_seconds() * 1000)
                status = "failed" if error_occurred else "completed"
                self._log.debug(f"Tool call {status}: {fn_name} duration={duration_ms}ms")
        except Exception:
            pass

        return result

    @staticmethod
    def serialize_tool_result(result: Any) -> str:
        try:
            return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        except Exception:
            return str(result)
