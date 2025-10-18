from __future__ import annotations
from pathlib import Path
from typing import Optional
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    func,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import json
from typing import List, Dict, Any, Tuple

# DB at project root (parent of 'core')
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = (BASE_DIR / "data" / "chat.db").resolve()

engine = create_engine(f"sqlite:///{DB_PATH}", future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()


class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False, default="New Thread")
    owner_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), index=True, nullable=False)
    role = Column(String(32), nullable=False)  # user | assistant | tool | system
    parent_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    content = Column(Text, nullable=False)
    model = Column(String(128), nullable=True)
    token_in = Column(Integer, nullable=True)
    token_out = Column(Integer, nullable=True)
    cost_usd = Column(String(32), nullable=True)
    agents = Column(Text, nullable=True)     # JSON string
    tools = Column(Text, nullable=True)      # JSON string
    api_calls = Column(Integer, nullable=True)
    meta = Column("metadata", Text, nullable=True)   # JSON string
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    thread = relationship("Thread", back_populates="messages")
    parent = relationship("Message", remote_side=[id])


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False)
    upto_message_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("thread_id", "upto_message_id", name="uq_thread_upto_message"),
        Index("ix_thread_upto_desc", "thread_id", "upto_message_id"),
    )


def _json_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return None


def init_chat_db() -> None:
    Base.metadata.create_all(bind=engine)
    print(f"Chat DB ready at {DB_PATH}")


# Convenience helpers

def create_thread(title: Optional[str] = None, owner_id: Optional[int] = None) -> Thread:
    with SessionLocal() as db:
        t = Thread(title=(title or "New Thread").strip() or "New Thread", owner_id=owner_id)
        db.add(t)
        db.commit()
        db.refresh(t)
        return t


def add_message(thread_id: int, role: str, content: str, **kwargs) -> Message:
    with SessionLocal() as db:
        m = Message(thread_id=thread_id, role=role, content=content, **kwargs)
        db.add(m)
        db.commit()
        db.refresh(m)
        return m


def get_message(message_id: int) -> Optional[Message]:
    with SessionLocal() as db:
        return db.get(Message, message_id)


def update_message(message_id: int, **fields) -> Optional[Message]:
    with SessionLocal() as db:
        m = db.get(Message, message_id)
        if not m:
            return None
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        db.commit()
        db.refresh(m)
        return m


def delete_message(message_id: int) -> bool:
    with SessionLocal() as db:
        m = db.get(Message, message_id)
        if not m:
            return False
        db.delete(m)
        db.commit()
        return True


def get_thread_messages(thread_id: int) -> list[Message]:
    with SessionLocal() as db:
        rows = (
            db.query(Message)
            .filter(Message.thread_id == thread_id)
            .order_by(Message.id.asc())
            .all()
        )
        return rows


def list_threads(owner_id: Optional[int] = None) -> list[Thread]:
    with SessionLocal() as db:
        q = db.query(Thread)
        if owner_id is not None:
            q = q.filter(Thread.owner_id == owner_id)
        threads = q.order_by(Thread.updated_at.desc()).all()
        filtered = []
        for t in threads:
            msg_count = db.query(func.count(Message.id)).filter(Message.thread_id == t.id).scalar() or 0
            if msg_count > 0:
                filtered.append(t)
        return filtered


def update_thread(thread_id: int, **fields) -> Optional[Thread]:
    with SessionLocal() as db:
        t = db.get(Thread, thread_id)
        if not t:
            return None
        for k, v in fields.items():
            if hasattr(t, k):
                setattr(t, k, v)
        db.commit()
        db.refresh(t)
        return t


def delete_thread(thread_id: int) -> bool:
    with SessionLocal() as db:
        t = db.get(Thread, thread_id)
        if not t:
            return False
        db.query(Summary).filter(Summary.thread_id == thread_id).delete(synchronize_session=False)
        db.delete(t)
        db.commit()
        return True


def cleanup_empty_threads(owner_id: Optional[int] = None) -> int:
    with SessionLocal() as db:
        q = db.query(Thread)
        if owner_id is not None:
            q = q.filter(Thread.owner_id == owner_id)
        threads = q.all()
        deleted = 0
        for t in threads:
            msg_count = db.query(func.count(Message.id)).filter(Message.thread_id == t.id).scalar() or 0
            if msg_count == 0:
                db.query(Summary).filter(Summary.thread_id == t.id).delete(synchronize_session=False)
                db.delete(t)
                deleted += 1
        db.commit()
        return deleted


# Summaries helpers

def add_summary(thread_id: int, upto_message_id: int, content: str) -> Summary:
    with SessionLocal() as db:
        s = Summary(thread_id=thread_id, upto_message_id=upto_message_id, content=content)
        db.add(s)
        db.commit()
        db.refresh(s)
        return s


def get_latest_summary(thread_id: int) -> Optional[Summary]:
    with SessionLocal() as db:
        row = (
            db.query(Summary)
            .filter(Summary.thread_id == thread_id)
            .order_by(Summary.upto_message_id.desc())
            .limit(1)
            .one_or_none()
        )
        return row
