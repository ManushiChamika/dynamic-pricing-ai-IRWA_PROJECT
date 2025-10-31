from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from core.agents.alert_service import api as alert_api
from backend.deps import get_current_user_for_alerts

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/incidents")
async def get_incidents(status: Optional[str] = None, current_user: Dict[str, Any] = Depends(get_current_user_for_alerts)) -> List[Dict[str, Any]]:
    owner_id = str(current_user["user_id"])
    try:
        incidents = await alert_api.list_incidents(status, None)
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/{incident_id}/ack")
async def acknowledge_incident(incident_id: str, current_user: Dict[str, Any] = Depends(get_current_user_for_alerts)) -> Dict[str, Any]:
    owner_id = str(current_user["user_id"])
    try:
        result = await alert_api.ack_incident(incident_id, owner_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, current_user: Dict[str, Any] = Depends(get_current_user_for_alerts)) -> Dict[str, Any]:
    owner_id = str(current_user["user_id"])
    try:
        result = await alert_api.resolve_incident(incident_id, owner_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
