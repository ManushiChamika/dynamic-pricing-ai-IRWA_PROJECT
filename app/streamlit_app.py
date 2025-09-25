# app/streamlit_app.py  (router/bootstrap)
# 0) Make the repo root importable BEFORE any project imports or Streamlit calls
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[1]  # points to <project-root>
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Now safe to import core modules
from core.db import init_db
from queue import SimpleQueue
ALERT_QUEUE = SimpleQueue()

init_db()

# 0.1) Load environment variables from .env (root first, then app/.env)
from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT / ".env", override=False)
load_dotenv(dotenv_path=HERE.parent / ".env", override=False)  # if you also keep app/.env

# 1) First Streamlit call
import streamlit as st
st.set_page_config(page_title="FluxPricer AI", page_icon="💹", layout="wide")

# 1.1) Async background loop helper (needed for Python 3.13 in Streamlit)
import asyncio, threading
def _ensure_bg_loop():
    """Create (once) a background asyncio loop and return it."""
    if "_bg_loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=loop.run_forever, daemon=True)
        t.start()
        st.session_state["_bg_loop"] = loop
    return st.session_state["_bg_loop"]

# 2) Style tweaks / sidebar branding
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] > div:first-child { display: none; }
    </style>
""", unsafe_allow_html=True)
with st.sidebar:
    st.markdown("### FluxPricer AI")

# 3) Project imports that rely on the repo root being on sys.path
from app.session_utils import ensure_session_from_cookie
from core.agents.alert_service import api as alerts  # <-- safe now

# 4) Session setup (do not force-stop if cookie manager hasn't initialized yet)
try:
    ensure_session_from_cookie()
except Exception:
    # If cookie manager hasn't rendered yet, continue; Home/Login will handle
    pass
st.session_state.setdefault("session", None)

# 5) Start the alert service once (schedule onto background loop)
if "_alerts_started" not in st.session_state:
    loop = _ensure_bg_loop()
    asyncio.run_coroutine_threadsafe(alerts.start(), loop)
    st.session_state["_alerts_started"] = True

# 6) Route to home page (which handles login/logout flow)
st.switch_page("pages/0_Home.py")
