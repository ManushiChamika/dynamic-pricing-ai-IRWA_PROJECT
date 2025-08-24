# app/_cookies.py
import streamlit as st
import extra_streamlit_components as stx

COOKIE_NAME = "fp_session"

def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        # Create ONE component instance and reuse it
        st.session_state["cookie_manager"] = stx.CookieManager(key="cookie-manager")
    return st.session_state["cookie_manager"]
