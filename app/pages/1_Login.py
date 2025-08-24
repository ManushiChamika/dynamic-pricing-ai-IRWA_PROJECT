# app/pages/1_Login.py
# --- path bootstrap ---
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in [HERE, *HERE.parents] if (p / "core").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ----------------------

import streamlit as st
from datetime import datetime, timedelta, timezone

from core.auth_db import init_db
from core.auth_service import authenticate, create_persistent_session
from app.session_utils import ensure_session_from_cookie, COOKIE_NAME, cookie_mgr



# 1) FIRST Streamlit call
st.set_page_config(page_title="Login — FluxPricer AI", page_icon="🔐", layout="centered")

# 2) Init DB and let ensure_session_from_cookie() be the ONLY place that mounts CookieManager
init_db()
ensure_session_from_cookie()  # mounts component, handles first-pass None/{} and sets session if cookie valid

# 3) If we were waiting for cookie commit from the previous submit:
if st.session_state.get("_await_cookie_commit"):
    if st.session_state.get("session"):
        # cookie was read & validated by ensure_session_from_cookie()
        st.session_state.pop("_await_cookie_commit", None)
        st.session_state["_post_login_redirect_ready"] = True
        st.rerun()
    else:
        st.info("Still finalizing sign-in…")
        st.stop()

# 4) Redirects
if st.session_state.get("_post_login_redirect_ready"):
    st.session_state.pop("_post_login_redirect_ready", None)
    st.switch_page("pages/0_Home.py")

if st.session_state.get("session"):
    st.switch_page("pages/0_Home.py")

# 5) UI
st.title("🔐 Login")
with st.form("login_form", clear_on_submit=False):
    email = st.text_input("Email", placeholder="you@example.com")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

# 6) Handle submit
if submitted:
    email_norm = (email or "").strip().lower()
    pw = (password or "").strip()

    if not email_norm or not pw:
        st.error("Email and password are required.")
    else:
        try:
            # 2FA removed: only email & password
            session = authenticate(email=email_norm, password=pw)
            st.session_state["session"] = session

            # Create server-side token
            token, _ = create_persistent_session(session["user_id"])

            # Set the cookie using the ONE CookieManager instance
            cm = cookie_mgr()  # singleton
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            cm.set(
                COOKIE_NAME,
                token,
                expires_at=expires_at,   # if your stx version doesn't support expires_at, switch to expires=expires_at
                max_age=7*24*60*60,
                path="/",
                same_site="Lax",
                # secure=True,  # enable on HTTPS in prod
            )

            # Allow this render to complete so browser commits the cookie.
            st.session_state["_await_cookie_commit"] = True
            st.success("Welcome! Finalizing sign-in…")
            st.stop()
        except Exception as e:
            st.error(str(e))
