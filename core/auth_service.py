# core/auth_service.py

from typing import Optional, Dict, Tuple, Any, Mapping, Union
from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from pydantic import BaseModel, EmailStr, Field, ValidationError

from .db import SessionLocal
from .models import User, SessionToken


# -------------------------
# Pydantic DTOs
# -------------------------

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="At least 8 characters")
    full_name: Optional[str] = None  # only used if your User model supports it


# -------------------------
# Auth primitives
# -------------------------

def authenticate(email: str, password: str) -> Optional[Dict[str, Any]]:
    with SessionLocal() as db:
        user = db.execute(
            select(User).where(User.email == email.lower())
        ).scalar_one_or_none()
        if not user:
            return None
        if not check_password_hash(user.password_hash, password):
            return None
        return {"user_id": user.id, "email": user.email}


def create_persistent_session(user_id: int, days: int = 7) -> Tuple[str, datetime]:
    token = create_session_token(user_id, ttl_hours=24 * days)
    expires = datetime.now(timezone.utc) + timedelta(days=days)
    return token, expires


# -------------------------
# Session token management
# -------------------------

def create_session_token(user_id: int, ttl_hours: int = 24) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=ttl_hours)
    with SessionLocal() as db:
        st = SessionToken(
            token=token,
            user_id=user_id,
            revoked=False,
            created_at=now,
            expires_at=expires,
        )
        db.add(st)
        db.commit()
    return token


def validate_session_token(token: str) -> Optional[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        row = db.execute(
            select(SessionToken).where(
                SessionToken.token == token,
                SessionToken.revoked == False,  # noqa: E712
                SessionToken.expires_at > now,
            )
        ).scalar_one_or_none()
        if not row:
            return None
        return {"user_id": row.user_id, "token": row.token, "expires_at": row.expires_at}


def revoke_session_token(token: str) -> bool:
    with SessionLocal() as db:
        res = db.execute(
            update(SessionToken)
            .where(SessionToken.token == token, SessionToken.revoked == False)  # noqa: E712
            .values(revoked=True)
        )
        db.commit()
        return (res.rowcount or 0) > 0


# -------------------------
# Profile
# -------------------------

def get_profile(user_id: int) -> Optional[Dict[str, Any]]:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user:
            return None
        data: Dict[str, Any] = {"user_id": user.id, "email": user.email}
        if hasattr(user, "full_name"):
            data["full_name"] = user.full_name
        if hasattr(user, "created_at"):
            data["created_at"] = user.created_at
        return data


# -------------------------
# Registration
# -------------------------

def register_user(
    data: Union[Mapping[str, Any], RegisterIn]
) -> Dict[str, Any]:
    """
    Accepts either a dict-like mapping or a RegisterIn instance.
    """
    try:
        if isinstance(data, RegisterIn):
            payload = data
        else:
            payload = RegisterIn(**dict(data))  # ensure mapping -> dict
    except ValidationError as ve:
        return {"ok": False, "error": ve.errors()}

    email = str(payload.email).lower()
    password_hash = generate_password_hash(payload.password)

    with SessionLocal() as db:
        try:
            existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if existing:
                return {"ok": False, "error": "Email already registered"}

            user_kwargs = {"email": email, "password_hash": password_hash}
            if hasattr(User, "full_name"):
                user_kwargs["full_name"] = payload.full_name

            user = User(**user_kwargs)
            db.add(user)
            db.commit()
            db.refresh(user)
            return {"ok": True, "user_id": user.id}
        except IntegrityError:
            db.rollback()
            return {"ok": False, "error": "Email already registered"}


# -------------------------
# Explicit exports
# -------------------------

__all__ = [
    "authenticate",
    "create_persistent_session",
    "create_session_token",
    "validate_session_token",
    "revoke_session_token",
    "get_profile",
    "RegisterIn",
    "register_user",
]
