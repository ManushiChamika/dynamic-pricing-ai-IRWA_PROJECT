from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel
from core.auth_service import (
    RegisterIn,
    register_user,
    authenticate,
    create_persistent_session,
    validate_session_token,
    revoke_session_token,
)

router = APIRouter(prefix="/api", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LogoutRequest(BaseModel):
    token: str | None = None


@router.post("/register")
def api_register(req: RegisterRequest):
    try:
        register_user(RegisterIn(email=req.email, full_name=req.username, password=req.password))
        user = authenticate(req.email, req.password)
        token, expires_at = create_persistent_session(user_id=user["user_id"])
        return {"ok": True, "token": token, "user": user, "expires_at": expires_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def api_login(req: LoginRequest):
    try:
        user = authenticate(req.email, req.password)
        token, expires_at = create_persistent_session(user_id=user["user_id"])
        return {"ok": True, "token": token, "user": user, "expires_at": expires_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
def api_me(token: str):
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"ok": True, "user": sess}


@router.post("/logout")
def api_logout(req: LogoutRequest, response: Response, fp_session: str | None = Cookie(default=None)):
    token = req.token or fp_session
    if not token:
        raise HTTPException(status_code=400, detail="No session token provided")
    revoke_session_token(token)
    response.delete_cookie("fp_session", path="/")
    return {"ok": True}
