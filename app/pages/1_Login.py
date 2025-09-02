# app/pages/1_Login.py

# --- path bootstrap (so imports work when launched from repo root or elsewhere) ---
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in [HERE, *HERE.parents] if (p / "core").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------------------------------------------------

import streamlit as st
from datetime import datetime, timedelta, timezone

from core.auth_db import init_db
from core.auth_service import (
    authenticate,
    create_persistent_session,
    validate_session_token,
)
from app.session_utils import (
    ensure_session_from_cookie,
    COOKIE_NAME,
    COOKIE_ATTRS,
    cookie_mgr,   # singleton accessor
)

# 1) First Streamlit call
st.set_page_config(page_title="Login — FluxPricer AI", page_icon="🔐", layout="centered")

# 2) Make sure the auth DB exists and the cookie manager is mounted exactly once.
#    ensure_session_from_cookie():
#      - mounts CookieManager (singleton) if needed
#      - reads cookie (if present) and populates st.session_state["session"] if token is valid
init_db()
ensure_session_from_cookie()

# 3) If we were waiting for cookie commit from the previous submit:
if st.session_state.get("_await_cookie_commit"):
    # When the browser reloads, ensure_session_from_cookie() above will validate and set session if cookie is there.
    if st.session_state.get("session") and st.session_state["session"].get("token"):
        # Final sanity: validate token again; if valid, clear the flag and redirect to Home.
        if validate_session_token(st.session_state["session"]["token"]):
            st.session_state.pop("_await_cookie_commit", None)
            st.switch_page("pages/0_Home.py")
            st.stop()
    # If we reach here, still waiting for the browser to send the cookie back.
    st.info("Finalizing sign-in…")
    st.stop()

# 4) Early session check — if already logged in, skip the login UI and go Home.
sess = st.session_state.get("session")
if sess and sess.get("token"):
    if validate_session_token(sess["token"]):
        st.switch_page("pages/0_Home.py")
        st.stop()

# 5) Login UI
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
            # Validate credentials (no 2FA in this flow)
            s = authenticate(email=email_norm, password=pw)
            # Persist session in DB (7 days) and in memory
            token, _ = create_persistent_session(s["user_id"], days=7)
            st.session_state["session"] = {**s, "token": token}

            # Write cookie using the single CookieManager instance mounted by ensure_session_from_cookie()
            cm = cookie_mgr()  # returns the singleton component instance
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

            # Some versions of extra-streamlit-components use "expires_at", older ones use "expires".
            # Using expires_at here (works on your setup per previous code). If needed, swap to expires=expires_at.
            cm.set(
                COOKIE_NAME,
                token,
                expires_at=expires_at,
                max_age=int(timedelta(days=7).total_seconds()),
                key="login_set",
                **COOKIE_ATTRS,
            )

            # Allow one render so the browser commits the cookie; then we rely on ensure_session_from_cookie()
            # in the next run to re-validate and redirect.
            st.session_state["_await_cookie_commit"] = True
            st.success("Welcome! Finalizing sign-in…")
            st.stop()

        except Exception as e:
            # Show auth errors (e.g., invalid credentials)
            st.error(str(e))
