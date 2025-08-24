from pathlib import Path
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime, func,
    UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# DB at project root (parent of 'core')
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = (BASE_DIR / "auth.db").resolve()

engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    totp_secret = Column(String(64))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    sessions = relationship("SessionToken", back_populates="user", cascade="all, delete-orphan")

class SessionToken(Base):
    __tablename__ = "session_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="sessions")

def init_db():
    Base.metadata.create_all(bind=engine)
