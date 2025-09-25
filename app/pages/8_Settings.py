# --- path bootstrap ---
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in [HERE, *HERE.parents] if (p / "core").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ----------------------

import streamlit as st
import sqlite3


def _open_app_db():
    return sqlite3.connect((ROOT / "app" / "data.db").as_posix(), check_same_thread=False)


def _ensure_settings(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()


def _get_setting(conn: sqlite3.Connection, key: str, default: str) -> str:
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    r = cur.fetchone()
    return r[0] if r and r[0] is not None else default


st.set_page_config(page_title="Auto-Apply Settings", page_icon="⚙️", layout="centered")
st.title("Auto‑Apply Settings")
st.write("Configure guardrails. Auto-apply will only accept proposals when margin ≥ min and price change ≤ max delta.")

conn = _open_app_db()
_ensure_settings(conn)

auto_apply_default = _get_setting(conn, "auto_apply", "false").lower() == "true"
min_margin_default = float(_get_setting(conn, "min_margin", "0.12"))
max_delta_default = float(_get_setting(conn, "max_delta", "0.10"))

auto_apply = st.checkbox("Enable auto-apply", value=auto_apply_default)
min_margin = st.number_input("Min margin", min_value=0.0, max_value=1.0, value=min_margin_default, step=0.01, format="%.2f")
max_delta = st.number_input("Max delta (relative)", min_value=0.0, max_value=1.0, value=max_delta_default, step=0.01, format="%.2f")

if st.button("Save"):
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ("auto_apply", "true" if auto_apply else "false"))
        cur.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ("min_margin", f"{min_margin:.2f}"))
        cur.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ("max_delta", f"{max_delta:.2f}"))
        conn.commit()
        st.success("Settings saved.")
    except Exception as e:
        st.error(f"Failed to save settings: {e}")

try:
    conn.close()
except Exception:
    pass




