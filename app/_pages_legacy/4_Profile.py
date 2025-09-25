# --- path bootstrap ---
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in [HERE, *HERE.parents] if (p / "core").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ----------------------

import streamlit as st
st.set_page_config(page_title="Profile — FluxPricer AI", page_icon="👤", layout="centered")

from core.auth_service import get_profile
from app.session_utils import ensure_session_from_cookie

# Restore session from cookie on refresh
ensure_session_from_cookie()

# ---- auth guard ----
session = st.session_state.get("session")
if not session:
    st.warning("Please login first.")
    st.stop()

# ---- simple CSS ----
st.markdown("""
<style>
.page-wrap {max-width: 820px; margin: 0 auto;}
.card {
  background:#111827; border:1px solid #1f2937; border-radius:16px; padding:18px;
  box-shadow: 0 4px 20px rgba(0,0,0,.25);
}
.kv {display:flex; gap:8px; align-items:center; margin:6px 0;}
.kv label {width:140px; color:#9ca3af;}
</style>
""", unsafe_allow_html=True)

# ---- load profile ----
try:
    prof = get_profile(session["user_id"])
except Exception as e:
    st.error(f"Could not load profile: {e}")
    st.stop()

st.markdown("<div class='page-wrap'>", unsafe_allow_html=True)

st.markdown(f"""
<div class="card">
  <div class="kv"><label>User ID</label><div>{prof.get("id","-")}</div></div>
  <div class="kv"><label>Email</label><div>{prof.get("email","-")}</div></div>
  <div class="kv"><label>Name</label><div>{prof.get("full_name") or "-"}</div></div>
</div>
""", unsafe_allow_html=True)

# Actions row
c1, c2 = st.columns([1, 1])

with c2:
    if st.button("Back to Home", key="btn_back_home"):
        st.switch_page("pages/0_Home.py")
