from typing import List, Dict, Any

try:
    from core.agents.agent_sdk.activity_log import activity_log
except Exception:
    activity_log = None  # type: ignore


def recent(limit: int = 50) -> List[Dict[str, Any]]:
    if activity_log is None:
        return []
    try:
        return activity_log.recent(limit)
    except Exception:
        return []
