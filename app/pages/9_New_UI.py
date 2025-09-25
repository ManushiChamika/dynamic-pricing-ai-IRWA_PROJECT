import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

# Page config
st.set_page_config(page_title="FluxPricer New UI (Preview)", page_icon="✨", layout="wide")

# Ensure cookie session if possible
try:
    from app.session_utils import ensure_session_from_cookie
    ensure_session_from_cookie(page_key="new_ui")
except Exception:
    pass

from app.ui.state.session import require_session

# Optionally start alerts engine (safe if already started elsewhere)
try:
    from core.agents.alert_service import api as alerts
    import asyncio
    from app.ui.services.runtime import ensure_bg_loop
    if "_alerts_started" not in st.session_state:
        loop = ensure_bg_loop()
        asyncio.run_coroutine_threadsafe(alerts.start(), loop)
        st.session_state["_alerts_started"] = True
except Exception:
    pass

# Require session
_ = require_session()

# Sidebar Navigation
st.sidebar.title("New UI")
section = st.sidebar.radio("Go to", ["Dashboard", "Incidents", "Activity", "Rules", "Settings"], index=0)

# Views
from app.ui.views import dashboard as v_dashboard
from app.ui.views import incidents as v_incidents
from app.ui.views import activity_view as v_activity
from app.ui.views import rules as v_rules
from app.ui.views import settings as v_settings

if section == "Dashboard":
    v_dashboard.view()
elif section == "Incidents":
    v_incidents.view()
elif section == "Activity":
    v_activity.view()
elif section == "Rules":
    v_rules.view()
elif section == "Settings":
    v_settings.view()
