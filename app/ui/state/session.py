from __future__ import annotations
import streamlit as st
from typing import Any, Dict


def require_session() -> Dict[str, Any]:
    sess = st.session_state.get("session")
    if not sess:
        st.warning("You must log in to access the new UI.")
        st.stop()
    return sess


def current_user() -> Dict[str, Any]:
    return st.session_state.get("session") or {}


def user_display_name() -> str:
    sess = current_user()
    full = (sess.get("full_name") or "").strip()
    if full:
        return full
    email = sess.get("email") or "user"
    return email.split("@")[0]
