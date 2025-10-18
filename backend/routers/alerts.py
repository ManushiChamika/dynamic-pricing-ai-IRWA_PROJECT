from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from core.agents.alert_service import api as alert_api

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/incidents")
async def get_incidents(status: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        incidents = await alert_api.list_incidents(status)
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/{incident_id}/ack")
async def acknowledge_incident(incident_id: str) -> Dict[str, Any]:
    try:
        result = await alert_api.ack_incident(incident_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str) -> Dict[str, Any]:
    try:
        result = await alert_api.resolve_incident(incident_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
