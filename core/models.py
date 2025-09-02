# core/models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# ---------------------------
# Auth DB models (SQLAlchemy)
# ---------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    tokens: Mapped[list["SessionToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class SessionToken(Base):
    __tablename__ = "session_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="tokens")


# -----------------------------------------
# Lightweight domain models (no DB mapping)
# -----------------------------------------

@dataclass
class MarketTick:
    """
    Lightweight tick used by alerting/agent paths.

    Note: Your data-collector persists ticks in app/data.db via aiosqlite,
    not through SQLAlchemy. This class is just for typing/inter-agent messages.
    """
    sku: str
    market: str = "DEFAULT"
    our_price: float = 0.0
    competitor_price: Optional[float] = None
    demand_index: Optional[float] = None
    source: str = "mock"
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PriceProposal:
    """
    Proposed price output by the optimizer. Kept as a dataclass only so that:
      - imports in scripts succeed
      - we can shuttle data across agents/pipelines
    Persist however you like (JSON/SQLite) outside this class.
    """
    sku: str
    current_price: float
    proposed_price: float
    margin: Optional[float] = None
    rationale: Optional[str] = None
    status: str = "PENDING"  # PENDING | ACCEPTED | APPLIED | REJECTED
    algorithm: Optional[str] = None      # <— added to match optimizer kwargs
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[str] = None

@dataclass
class AlertEvent:
    """
    Minimal alert event for notifier/bus flows.
    """
    sku: str
    kind: str
    message: str
    severity: str = "info"  # info | warn | crit
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
