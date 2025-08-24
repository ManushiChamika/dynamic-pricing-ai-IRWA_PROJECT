# 1) Safe: sys.path bootstrap BEFORE any Streamlit calls
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 2) First Streamlit call must be set_page_config
import streamlit as st
st.set_page_config(page_title="FluxPricer AI", page_icon="💹", layout="wide")

# --- Hide default "streamlit app" text in sidebar ---
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] > div:first-child {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# --- (Optional) Add your own sidebar branding ---
with st.sidebar:
    st.markdown("### FluxPricer AI")

# 3) Now it's safe to import/call helpers that render components
from app.session_utils import ensure_session_from_cookie
ensure_session_from_cookie()

# 4) Optional: init session dict and route to Home
st.session_state.setdefault("session", None)
st.switch_page("pages/0_Home.py")
