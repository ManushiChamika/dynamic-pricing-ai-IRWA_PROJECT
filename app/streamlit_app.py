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
# Debug-safe behavior: do NOT perform an unconditional page switch.
# Some local dev setups and Streamlit reruns can end up redirecting unexpectedly.
# To enable the original behavior set the session flag `_auto_home_redirect = True`.
st.session_state.setdefault("_auto_home_redirect", False)

# Show a lightweight debug hint in the sidebar so we can see this file ran.
with st.sidebar.expander("App bootstrap (debug)", expanded=False):
    st.write({
        "session": bool(st.session_state.get("session")),
        "_auto_home_redirect": st.session_state.get("_auto_home_redirect"),
    })

if st.session_state.get("_auto_home_redirect"):
    st.info("Auto-redirecting to Home (flag enabled)")
    st.switch_page("pages/0_Home.py")
else:
    st.sidebar.info("Auto-redirect disabled — dashboard/pages will render directly (debug)")

print("streamlit_app.py: module imported — auto_home_redirect=", st.session_state.get("_auto_home_redirect"))
# Append a persistent runtime debug record so we can inspect logs after restarts
try:
    from datetime import datetime
    import pathlib
    logp = pathlib.Path.cwd() / "runtime_debug.log"
    logp.write_text(f"{datetime.utcnow().isoformat()} streamlit_app imported auto_home_redirect={st.session_state.get('_auto_home_redirect')}\n", encoding="utf-8", )
except Exception:
    pass
