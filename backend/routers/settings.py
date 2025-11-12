from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from core.auth_service import validate_session_token

router = APIRouter(prefix="/api", tags=["settings"])

SETTINGS_STORE: Dict[int, Dict[str, Any]] = {}


def _default_settings() -> Dict[str, Any]:
    import os
    def _dev_enabled() -> bool:
        try:
            if os.getenv("PYTEST_CURRENT_TEST") is not None:
                return os.environ.get("DEV_MODE", "").lower() in {"1", "true", "yes", "on"}
            raw = os.environ.get("DEV_MODE")
            if raw is not None:
                try:
                    return raw.lower() in {"1", "true", "yes", "on"}
                except Exception:
                    return False
            from core.settings import get_settings
            return bool(getattr(get_settings(), "dev_mode", False))
        except Exception:
            try:
                return os.environ.get("DEV_MODE", "").lower() in {"1", "true", "yes", "on"}
            except Exception:
                return False
    dev = _dev_enabled()
    return {
        "show_model_tag": True,
        "show_timestamps": bool(dev),
        "show_metadata_panel": bool(dev),
        "show_thinking": bool(dev),
        "theme": "dark",
        "streaming": "sse",
        "mode": "user",
    }



def _get_user_settings(token: Optional[str]) -> Dict[str, Any]:
    user_id: Optional[int] = None
    if token:
        sess = validate_session_token(token)
        user_id = int(sess["user_id"]) if sess else None
    if user_id is not None and user_id in SETTINGS_STORE:
        return SETTINGS_STORE[user_id]
    return _default_settings()


class UpdateSettingsRequest(BaseModel):
    token: Optional[str] = None
    settings: Dict[str, Any]


@router.get("/settings")
def api_get_settings(token: Optional[str] = None):
    return {"ok": True, "settings": _get_user_settings(token)}


@router.put("/settings")
def api_update_settings(req: UpdateSettingsRequest):
    sess = validate_session_token(req.token) if req.token else None
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    uid = int(sess["user_id"])
    cur = SETTINGS_STORE.get(uid, _default_settings())
    allowed = _default_settings().keys()
    cur.update({k: v for k, v in req.settings.items() if k in allowed})
    SETTINGS_STORE[uid] = cur
    return {"ok": True, "settings": cur}


def get_user_settings(token: Optional[str]) -> Dict[str, Any]:
    return _get_user_settings(token)
