from typing import Optional
from datetime import datetime, timedelta
import secrets

from argon2 import PasswordHasher
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from .auth_db import SessionLocal, User, SessionToken

ph = PasswordHasher()
SESSION_DAYS = 7  # persistent login duration


class RegisterIn(BaseModel):
    email: str
    full_name: Optional[str] = None
    password: str


def _hash(pw: str) -> str:
    return ph.hash(pw)


def _verify(pw: str, h: str) -> bool:
    try:
        ph.verify(h, pw)
        return True
    except Exception:
        return False


# ---------- Register ----------
def register_user(inp: RegisterIn) -> None:
    email_norm = (inp.email or "").strip().lower()
    pw = (inp.password or "").strip()

    # validate email
    try:
        validate_email(email_norm)
    except EmailNotValidError as e:
        raise ValueError(str(e))

    if len(pw) < 10:
        raise ValueError("Password must be at least 10 characters")

    with SessionLocal() as db:
        if db.query(User).filter(User.email == email_norm).first():
            raise ValueError("Email already registered")
        u = User(
            email=email_norm,
            full_name=(inp.full_name or "").strip() or None,
            hashed_password=_hash(pw),
        )
        db.add(u)
        db.commit()


# ---------- Login ----------
def authenticate(email: str, password: str) -> dict:
    email_norm = (email or "").strip().lower()
    pw = (password or "").strip()

    with SessionLocal() as db:
        u = db.query(User).filter(User.email == email_norm).first()
        if not u or not getattr(u, "is_active", True):
            raise ValueError("Invalid email or password")
        try:
            ph.verify(u.hashed_password, pw)
        except Exception:
            raise ValueError("Invalid email or password")

        return {"user_id": u.id, "email": u.email, "full_name": u.full_name}


# ---------- Profile ----------
def get_profile(user_id: int) -> dict:
    with SessionLocal() as db:
        u: Optional[User] = db.get(User, user_id)
        if not u:
            raise ValueError("User not found")
        return {"id": u.id, "email": u.email, "full_name": u.full_name}


# ---------- Persistent session tokens ----------
def create_persistent_session(user_id: int) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_DAYS)
    with SessionLocal() as db:
        db.add(SessionToken(user_id=user_id, token=token, expires_at=expires_at))
        db.commit()
    return token, expires_at


def validate_session_token(token: str) -> dict | None:
    now = datetime.utcnow()
    with SessionLocal() as db:
        row: Optional[SessionToken] = db.query(SessionToken).filter_by(token=token, revoked=False).first()
        if not row or row.expires_at <= now:
            return None

        u: Optional[User] = db.get(User, row.user_id)
        if not u or not getattr(u, "is_active", True):
            return None

        return {"user_id": u.id, "email": u.email, "full_name": u.full_name}


def revoke_session_token(token: str) -> None:
    with SessionLocal() as db:
        row: Optional[SessionToken] = db.query(SessionToken).filter_by(token=token).first()
        if row:
            row.revoked = True
            db.add(row)
            db.commit()
