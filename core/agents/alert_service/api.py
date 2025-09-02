# core/agents/alert_service/api.py
from typing import Optional, Dict, Any, List

from .repo import Repo
from .engine import AlertEngine
from .schemas import RuleSpec
from .config import merge_defaults_db, for_ui  # load_runtime_defaults no longer needed

# Singletons for this process
_repo = Repo()
_engine = AlertEngine(_repo)
_started = False  # idempotent start guard


def _dump(model):
    fn = getattr(model, "model_dump", None)
    if callable(fn):
        return fn()
    return model.dict()

# ---------- Lifecycle ----------
async def start() -> None:
    global _started
    if _started:
        return
    await _repo.init()
    await _engine.start()
    _started = True

async def reload_rules() -> None:
    """Hot-reload rules in the running engine."""
    if hasattr(_engine, "reload_rules"):
        await _engine.reload_rules()    # type: ignore[attr-defined]
    elif hasattr(_engine, "_load_rules"):
        await _engine._load_rules()     # type: ignore[attr-defined]

# ---------- Incidents ----------
async def list_incidents(status: Optional[str] = None) -> List[Dict[str, Any]]:
    return await _repo.list_incidents(status)

async def ack_incident(incident_id: str) -> Dict[str, Any]:
    await _repo.set_status(incident_id, "ACKED")
    return {"ok": True, "id": incident_id, "status": "ACKED"}

async def resolve_incident(incident_id: str) -> Dict[str, Any]:
    await _repo.set_status(incident_id, "RESOLVED")
    return {"ok": True, "id": incident_id, "status": "RESOLVED"}

# ---------- Rules ----------
async def create_rule(spec: Dict[str, Any]) -> Dict[str, Any]:
    rule = RuleSpec(**spec)             # validate
    await _repo.upsert_rule(rule)
    await reload_rules()
    return {"ok": True, "id": rule.id}

async def list_rules() -> List[Dict[str, Any]]:
    rows = await _repo.list_rules()
    return [_dump(r.spec) for r in rows]

# ---------- Channel Settings ----------
async def get_settings() -> Dict[str, Any]:
    """
    Merge env-based defaults with DB overrides (DB wins),
    then return a UI-safe (secrets-masked) dict.
    """
    merged = await merge_defaults_db(_repo)
    return for_ui(merged)

async def save_settings(d: Dict[str, Any]) -> bool:
    await _repo.save_channel_settings(d)
    return True
