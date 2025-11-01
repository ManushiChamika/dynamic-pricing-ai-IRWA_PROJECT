import os
import sqlite3
import tempfile
from pathlib import Path

from core.agents.user_interact import tools as tools_mod


def test_list_inventory_items_without_owner_returns_guidance_message(monkeypatch):
    monkeypatch.setattr(tools_mod, "get_owner_id", lambda: None)
    res = tools_mod.list_inventory_items()
    assert isinstance(res, dict)
    assert "message" in res
    assert "No inventory found for your account" in res["message"]


def test_list_inventory_items_empty_for_owner_returns_guidance_message(monkeypatch):
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE product_catalog (
                    sku TEXT,
                    title TEXT,
                    currency TEXT,
                    current_price REAL,
                    cost REAL,
                    stock INTEGER,
                    updated_at TEXT,
                    owner_id TEXT
                )
                """
            )
            conn.commit()
        monkeypatch.setattr(tools_mod, "get_db_paths", lambda: {"app": Path(db_path), "market": Path(db_path)})
        monkeypatch.setattr(tools_mod, "get_owner_id", lambda: "user-1")
        res = tools_mod.list_inventory_items()
        assert isinstance(res, dict)
        assert "message" in res
        assert "Your inventory is currently empty" in res["message"]
    finally:
        try:
            os.remove(db_path)
        except Exception:
            pass
