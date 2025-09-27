from __future__ import annotations
import sqlite3
from pathlib import Path
import streamlit as st
from app.ui.theme.inject import apply_theme


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
	try:
		cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
		return cur.fetchone() is not None
	except Exception:
		return False


def _app_db_path() -> Path:
	root = Path(__file__).resolve().parents[3]
	return root / "app" / "data.db"


def view() -> None:
	apply_theme(False)
	st.subheader("🧭 Decision Log")

	# Filters
	col1, col2, col3 = st.columns([2, 1, 1])
	with col1:
		sku = st.text_input("SKU contains", "")
	with col2:
		limit = st.number_input("Limit", min_value=10, max_value=500, value=100, step=10)
	with col3:
		actor = st.text_input("Actor", "")

	dbp = _app_db_path()
	rows = []
	try:
		with sqlite3.connect(dbp.as_posix()) as conn:
			conn.row_factory = sqlite3.Row
			if not _table_exists(conn, "decision_log"):
				st.info("No decisions yet.")
				return
			q = (
				"SELECT ts, sku, old_price, new_price, margin, algorithm, decision, actor "
				"FROM decision_log"
			)
			params = []
			clauses = []
			if sku:
				clauses.append("sku LIKE ?")
				params.append(f"%{sku}%")
			if actor:
				clauses.append("actor LIKE ?")
				params.append(f"%{actor}%")
			if clauses:
				q += " WHERE " + " AND ".join(clauses)
			q += " ORDER BY ts DESC LIMIT ?"
			params.append(int(limit))
			rows = [dict(r) for r in conn.execute(q, params).fetchall()]
	except Exception as e:
		st.error(f"DB error: {e}")
		return

	if not rows:
		st.info("No matching decision records.")
		return

	# Render table
	st.dataframe(rows, use_container_width=True)
