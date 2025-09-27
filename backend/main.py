from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.auth_db import init_db
from core.auth_service import RegisterIn, register_user, authenticate, create_persistent_session, validate_session_token

app = FastAPI(title="FluxPricer Auth API")

# CORS for local React dev on any localhost/127.0.0.1 port
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str | None = None  # maps to full_name for now


class LoginRequest(BaseModel):
    email: str
    password: str


@app.on_event("startup")
def _startup():
    init_db()


@app.post("/api/register")
def api_register(req: RegisterRequest):
    try:
        register_user(RegisterIn(email=req.email, full_name=req.username, password=req.password))
        # Create a session on successful registration
        user = authenticate(req.email, req.password)
        token, expires_at = create_persistent_session(user_id=user["user_id"])
        return {"ok": True, "token": token, "user": user, "expires_at": expires_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/login")
def api_login(req: LoginRequest):
    try:
        user = authenticate(req.email, req.password)
        token, expires_at = create_persistent_session(user_id=user["user_id"])
        return {"ok": True, "token": token, "user": user, "expires_at": expires_at.isoformat()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/me")
def api_me(token: str):
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"ok": True, "user": sess}
