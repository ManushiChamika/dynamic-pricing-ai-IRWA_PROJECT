# --- path bootstrap ---
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in [HERE, *HERE.parents] if (p / "core").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ----------------------

import streamlit as st
from datetime import timedelta  # (not required, just here if you later add auto-login)
st.set_page_config(page_title="Register — FluxPricer AI", page_icon="🪪", layout="centered")

from core.auth_db import init_db
from core.auth_service import RegisterIn, register_user
from app.session_utils import ensure_session_from_cookie

# Init + cookie-based session restore
init_db()
ensure_session_from_cookie()

# Already logged in? Go home.
if st.session_state.get("session"):
    st.switch_page("pages/0_Home.py")
    st.stop()

st.title("🪪 Create Account")
with st.form("register_form", clear_on_submit=False):
    email = st.text_input("Email", placeholder="you@example.com")
    full_name = st.text_input("Full name (optional)")
    password = st.text_input("Password (≥10 chars)", type="password")
    submitted = st.form_submit_button("Register")

if submitted:
    email_norm = (email or "").strip().lower()
    full_name_norm = (full_name or "").strip() or None
    pw = (password or "").strip()

    # Quick client-side checks (server will re-validate anyway)
    if not email_norm:
        st.error("Email is required.")
    elif len(pw) < 10:
        st.error("Password must be at least 10 characters.")
    else:
        try:
            register_user(RegisterIn(
                email=email_norm,
                full_name=full_name_norm,
                password=pw,
            ))
            st.success("Account created. Please log in.")
            st.switch_page("pages/1_Login.py")
            st.stop()
        except Exception as e:
            # Pass through the nice messages from register_user (email exists, invalid email, etc.)
            st.error(str(e))
