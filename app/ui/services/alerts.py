from typing import Any, Dict, List, Optional

try:
    from core.agents.alert_service import api as alerts
except Exception:
    alerts = None  # type: ignore


async def list_incidents(status: Optional[str] = None) -> List[Dict[str, Any]]:
    if alerts is None:
        return []
    return await alerts.list_incidents(status)


async def ack_incident(incident_id: str) -> Dict[str, Any]:
    if alerts is None:
        return {"ok": False, "id": incident_id, "error": "alerts api unavailable"}
    return await alerts.ack_incident(incident_id)


async def resolve_incident(incident_id: str) -> Dict[str, Any]:
    if alerts is None:
        return {"ok": False, "id": incident_id, "error": "alerts api unavailable"}
    return await alerts.resolve_incident(incident_id)


async def list_rules() -> List[Dict[str, Any]]:
    if alerts is None:
        return []
    return await alerts.list_rules()


async def reload_rules() -> bool:
    if alerts is None:
        return False
    try:
        await alerts.reload_rules()
        return True
    except Exception:
        return False


async def create_rule(spec: Dict[str, Any]) -> Dict[str, Any]:
    if alerts is None:
        return {"ok": False, "error": "alerts api unavailable"}
    return await alerts.create_rule(spec)


async def get_settings() -> Dict[str, Any]:
    if alerts is None:
        return {}
    return await alerts.get_settings()


async def save_settings(d: Dict[str, Any]) -> bool:
    if alerts is None:
        return False
    return await alerts.save_settings(d)
