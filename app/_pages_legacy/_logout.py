# app/pages/_logout.py
import streamlit as st
from app.session_utils import ensure_session_from_cookie, cookie_mgr, clear_session_cookie
from core.auth_service import revoke_session_token

st.set_page_config(page_title="Logout — FluxPricer AI", page_icon="👋", layout="centered")

# Restore from cookie if present
ensure_session_from_cookie("logout")

# Mount CookieManager so its JS can clear cookies on this page
cm = cookie_mgr()

st.header("Log out")
st.write("Are you sure you want to log out?")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("✅ Yes, log out", key="logout_yes"):
        session = st.session_state.get("session")

        if session:
            # Revoke server-side (best effort)
            tok = session.get("token")
            if tok:
                try:
                    revoke_session_token(tok)
                except Exception:
                    pass

            # Prevent immediate cookie-based restore and drop in-memory session
            st.session_state.pop("session", None)
            st.session_state["_skip_cookie_restore_once"] = True

            # Clear the browser cookie (expires_at + max_age=0 + delete with exact attrs)
            clear_session_cookie()

            st.success("You’ve been logged out.")
            st.caption("Cookie cleared. Redirecting…")
            st.markdown('<meta http-equiv="refresh" content="1.2;url=/">', unsafe_allow_html=True)
        else:
            # Not logged in → send user to Login with a message
            st.session_state["flash_info"] = "Please log in first."
            st.switch_page("pages/1_Login.py")

with col2:
    if st.button("❌ Cancel", key="logout_cancel"):
        # If logged in, go home; else go to Login
        if st.session_state.get("session"):
            st.switch_page("pages/0_Home.py")
        else:
            st.switch_page("pages/1_Login.py")
