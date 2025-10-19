from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from core.agents.alert_service import api as alert_api
from core.auth_service import validate_session_token

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/incidents")
async def get_incidents(status: Optional[str] = None, token: Optional[str] = None) -> List[Dict[str, Any]]:
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    owner_id = str(sess["user_id"])
    
    try:
        incidents = await alert_api.list_incidents(status, None)
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/{incident_id}/ack")
async def acknowledge_incident(incident_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    owner_id = str(sess["user_id"])
    
    try:
        result = await alert_api.ack_incident(incident_id, owner_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    owner_id = str(sess["user_id"])
    
    try:
        result = await alert_api.resolve_incident(incident_id, owner_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
