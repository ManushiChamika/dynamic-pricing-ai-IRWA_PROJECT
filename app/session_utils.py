# app/session_utils.py
import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta, timezone
from core.auth_service import validate_session_token

COOKIE_NAME = "fp_session"

# Must match how the cookie is created (your row shows Lax, secure False, no domain, path "/")
COOKIE_ATTRS = {
    "path": "/",          # required
    "samesite": "Lax",    # exactly as created
    "secure": False,      # exactly as created (True only on HTTPS prod if you used it)
    # DO NOT set "domain" for localhost (browsers ignore/forbid it)
}

def cookie_mgr() -> stx.CookieManager:
    if "_cookie_mgr" not in st.session_state:
        # one instance per Streamlit session; reuse everywhere
        st.session_state["_cookie_mgr"] = stx.CookieManager(key="cookie-manager")
    return st.session_state["_cookie_mgr"]

def set_session_cookie(token: str) -> None:
    cm = cookie_mgr()
    cm.set(COOKIE_NAME, token, key="set_session_cookie", **COOKIE_ATTRS)

def clear_session_cookie() -> None:
    """
    Clear fp_session using the same attributes it was created with.
    We do: expires_at in the past, max_age=0, and delete — all three,
    plus a hostOnly 'no-attrs' pass for older browsers.
    """
    cm = cookie_mgr()

    # 1) expire in the past (UTC)
    past = datetime.now(timezone.utc) - timedelta(days=1)
    try:
        cm.set(COOKIE_NAME, "", expires_at=past, key="expire_cookie", **COOKIE_ATTRS)
    except TypeError:
        cm.set(COOKIE_NAME, "", expires_at=past, key="expire_cookie")

    # 2) set max_age=0
    try:
        cm.set(COOKIE_NAME, "", max_age=0, key="maxage_cookie", **COOKIE_ATTRS)
    except TypeError:
        cm.set(COOKIE_NAME, "", max_age=0, key="maxage_cookie")

    # 3) explicit delete with matching attrs
    try:
        cm.delete(COOKIE_NAME, key="delete_cookie", **COOKIE_ATTRS)
    except TypeError:
        cm.delete(COOKIE_NAME)

    # 4) (defensive) hostOnly delete with *no attrs* — useful on localhost
    try:
        cm.delete(COOKIE_NAME, key="delete_cookie_hostonly")
    except Exception:
        pass

def ensure_session_from_cookie(page_key: str = "root") -> bool:
    """Attempt to hydrate st.session_state['session'] from the fp_session cookie.

    Returns True when the CookieManager has responded (regardless of whether a valid
    cookie was found). Returns False while the CookieManager component is still
    mounting and has not provided any cookie data yet.
    """

    if st.session_state.pop("_skip_cookie_restore_once", False):
        return True
    if st.session_state.get("session"):
        return True

    # Use cookie manager to restore session when available
    cm = cookie_mgr()
    import time
    unique_key = f"get_all_{page_key}_{int(time.time() * 1000000)}"
    cookies = cm.get_all(key=unique_key)
    if cookies is None:
        # Cookie manager not ready yet; allow page to continue
        return False

    token = cookies.get(COOKIE_NAME)
    if not token:
        st.session_state.pop("session_token", None)
        return True

    try:
        sess = validate_session_token(token)
    except Exception:
        sess = None

    if sess:
        st.session_state["session"] = sess
        st.session_state["session_token"] = token
        return True

    st.session_state.pop("session_token", None)
    return True
