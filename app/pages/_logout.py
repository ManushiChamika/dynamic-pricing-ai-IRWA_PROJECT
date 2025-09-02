import streamlit as st
from app.session_utils import clear_session_cookie
from core.auth_service import revoke_session_token

st.title("Logout")

tok = (st.session_state.get("session") or {}).get("token")
if tok:
    try:
        revoke_session_token(tok)
    except Exception:
        pass

st.session_state.pop("session", None)
st.session_state["_skip_cookie_restore_once"] = True
clear_session_cookie()
st.success("Logged out.")
