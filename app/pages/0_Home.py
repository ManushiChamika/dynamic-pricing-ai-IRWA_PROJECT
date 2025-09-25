from app.session_utils import ensure_session_from_cookie
import streamlit as st

# ————————————————————————————————————————————————————————————————
# Session bootstrap and routing
# ————————————————————————————————————————————————————————————————
try:
    ensure_session_from_cookie("home")
except Exception:
    # If cookie manager hasn't rendered yet, continue
    pass

# Check if user is authenticated and redirect accordingly
if st.session_state.get("session"):
    # User is logged in - redirect to dashboard
    st.switch_page("pages/dashboard.py")
else:
    # User is not logged in - redirect to landing page
    st.switch_page("pages/0_Landing.py")