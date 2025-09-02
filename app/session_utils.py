import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta, timezone
from core.auth_service import validate_session_token, revoke_session_token

COOKIE_NAME = "fp_session"
COOKIE_ATTRS = {"path": "/", "same_site": "Lax", "secure": False}  # set secure=True on HTTPS

def cookie_mgr() -> stx.CookieManager:
    if "_cookie_mgr" not in st.session_state:
        st.session_state["_cookie_mgr"] = stx.CookieManager(key="cookie-manager")
    return st.session_state["_cookie_mgr"]

def set_session_cookie(token: str) -> None:
    cookie_mgr().set(COOKIE_NAME, token, key="set_session_cookie", **COOKIE_ATTRS)

def clear_session_cookie() -> None:
    cm = cookie_mgr()
    past = datetime.now(timezone.utc) - timedelta(days=1)
    try: cm.set(COOKIE_NAME, "", expires_at=past, key="expire_cookie", **COOKIE_ATTRS)
    except TypeError: cm.set(COOKIE_NAME, "", expires_at=past, key="expire_cookie")
    try: cm.set(COOKIE_NAME, "", max_age=0, key="maxage_cookie", **COOKIE_ATTRS)
    except TypeError: cm.set(COOKIE_NAME, "", max_age=0, key="maxage_cookie")
    try: cm.delete(COOKIE_NAME, key="delete_cookie", **COOKIE_ATTRS)
    except TypeError: cm.delete(COOKIE_NAME)
    try: cm.delete(COOKIE_NAME, key="delete_cookie_hostonly")
    except Exception: pass

def ensure_session_from_cookie(page_key: str = "root") -> None:
    if st.session_state.pop("_skip_cookie_restore_once", False):
        return
    if st.session_state.get("session"):
        return
    cookies = cookie_mgr().get_all(key=f"get_all_{page_key}")
    if not cookies:
        st.stop()
    token = cookies.get(COOKIE_NAME)
    if not token:
        return
    sess = validate_session_token(token)
    if sess:
        st.session_state["session"] = {**sess, "token": token}
