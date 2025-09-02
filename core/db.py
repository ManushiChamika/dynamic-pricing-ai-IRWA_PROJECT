# core/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# One DB URL for the whole app (SQLite by default)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    # SQLite needs this when used across threads (Streamlit, BG tasks)
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)

# Declarative base
class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """
    Import models and create all tables if they don't exist.
    Safe to call multiple times.
    """
    # Ensure models are registered with Base before create_all()
    from . import models  # noqa: F401
    Base.metadata.create_all(engine)


# --- Compatibility alias for legacy imports ---
# Some modules (e.g., core/repositories/tick_repo.py) used to import
# `MarketTickRow` from core.db. We expose an alias so those continue to work.
try:
    from .models import MarketTick as MarketTickRow  # type: ignore
except Exception:
    # If models aren't importable yet (during certain tooling phases),
    # just skip the alias; init_db() will import models when needed.
    pass


__all__ = [
    "DATABASE_URL",
    "engine",
    "SessionLocal",
    "Base",
    "init_db",
    # Export alias so legacy imports succeed
    "MarketTickRow",
]
