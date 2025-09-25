import streamlit as st
import pandas as pd
import asyncio
import threading
import sys
import pathlib
from concurrent.futures import TimeoutError as FuturesTimeout

# ---- Page Config ----
st.set_page_config(page_title="Activity Monitor - Dynamic Pricing", page_icon="📋", layout="wide")

# ---- Custom CSS ----
st.markdown("""
<style>
.stApp { background-color: #a6bdde; color: #000000; }
.stMetric { background-color: #7da3c3; border-radius: 10px; padding: 10px; color: #000000; }
.stSidebar { background-color: #7da3c3; color: #000000; }
.activity-item {
    background-color: #7da3c3;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    border-left: 4px solid #5896ed;
}
.incident-open {
    border-left-color: #ff4444;
}
.incident-resolved {
    border-left-color: #44ff44;
}
</style>
""", unsafe_allow_html=True)

# =================
# Session Gate/Init
# =================
if "session" not in st.session_state or st.session_state["session"] is None:
    st.warning("⚠ You must log in first!")
    st.stop()

user_session = st.session_state["session"]
user_name = user_session.get("full_name", "User")
user_email = user_session.get("email") or "anonymous@example.com"
full_name = (user_session.get("full_name") or "").strip()

if full_name:
    user_name = full_name
else:
    user_name = user_email.split("@")[0]

# ====================
# Page Header
# ====================
st.markdown(f"<h1 style='color:#000000;'>📋 Activity Monitor</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color:#000000;'>System Activity & Incidents, <b>{user_name}</b></h3>", unsafe_allow_html=True)

# Navigation
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/3_Dashboard.py")
with col2:
    if st.button("📊 Analytics", use_container_width=True):
        st.switch_page("pages/4_Analytics.py")
with col3:
    if st.button("🤖 AI Assistant", use_container_width=True):
        st.switch_page("pages/5_AI_Assistant.py")
with col4:
    st.button("📋 Activity", disabled=True, use_container_width=True)

st.markdown("---")

# ============================================================================ #
# ==================  🔧 EXTRAS: Alerts Engine & Incidents  ================== #
# ============================================================================ #

# Make 'core' package importable (only if it exists)
try:
    HERE = pathlib.Path(__file__).resolve()
except NameError:
    # Fallback for some environments where _file_ may not be defined
    HERE = pathlib.Path.cwd()

ROOT = next((p for p in [HERE, *HERE.parents] if (p / "core").exists()), None)
if ROOT and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import optimizer hub for background processing
try:
    from core.agents.user_interact.hub import OptimizerHub
except Exception:
    class OptimizerHub:
        async def start(self):
            pass

# Background asyncio loop (to call alert APIs safely from Streamlit)
def _ensure_bg_loop():
    if "_bg_loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=loop.run_forever, daemon=True)
        t.start()
        st.session_state["_bg_loop"] = loop
    return st.session_state["_bg_loop"]

if "_ui_hub" not in st.session_state:
    st.session_state["_ui_hub"] = OptimizerHub()
    asyncio.run_coroutine_threadsafe(
        st.session_state["_ui_hub"].start(),
        _ensure_bg_loop()
    )

def run_async(coro, timeout: float | None = 10.0):
    loop = _ensure_bg_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        return fut.result(timeout=timeout)
    except FuturesTimeout:
        return None
    except Exception:
        return None

# Start alerts engine once (so incidents flow even on the dashboard)
alerts = None
try:
    from core.agents.alert_service import api as _alerts
    alerts = _alerts
except Exception:
    alerts = None

if alerts:
    if "_alerts_started" not in st.session_state:
        try:
            asyncio.run_coroutine_threadsafe(alerts.start(), _ensure_bg_loop())
            st.session_state["_alerts_started"] = True
        except Exception:
            st.session_state["_alerts_started"] = False

# ====================
# Incidents Section
# ====================
st.subheader("🔔 System Incidents")

if alerts:
    col1, col2 = st.columns([2, 1])
    
    with col2:
        if st.button("🔄 Refresh Incidents", use_container_width=True):
            st.rerun()
    
    try:
        rows = run_async(alerts.list_incidents(None)) or []
    except Exception:
        rows = []
    
    # Metrics
    open_incidents = sum(1 for r in rows if r.get("status") == "OPEN")
    resolved_incidents = sum(1 for r in rows if r.get("status") == "RESOLVED")  
    total_incidents = len(rows)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🚨 Open Incidents", open_incidents, delta=None)
    with col2:
        st.metric("✅ Resolved Today", resolved_incidents, delta=None)
    with col3:
        st.metric("📊 Total Incidents", total_incidents, delta=None)
    
    if rows:
        st.markdown("### Incident Details")
        
        # Create tabs for different incident views
        tab1, tab2, tab3 = st.tabs(["🚨 Active", "✅ Resolved", "📊 All"])
        
        with tab1:
            active_incidents = [r for r in rows if r.get("status") == "OPEN"]
            if active_incidents:
                for incident in active_incidents:
                    with st.container():
                        st.markdown(f"""
                        <div class="activity-item incident-open">
                            <strong>🚨 {incident.get('title', 'Untitled Incident')}</strong><br>
                            <small>ID: {incident.get('id', 'N/A')} | Severity: {incident.get('severity', 'Unknown')} | Created: {incident.get('created_at', 'Unknown')}</small><br>
                            <em>{incident.get('description', 'No description available')}</em>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.success("🎉 No active incidents! All systems are running smoothly.")
        
        with tab2:
            resolved_incidents = [r for r in rows if r.get("status") == "RESOLVED"]
            if resolved_incidents:
                for incident in resolved_incidents:
                    with st.container():
                        st.markdown(f"""
                        <div class="activity-item incident-resolved">
                            <strong>✅ {incident.get('title', 'Untitled Incident')}</strong><br>
                            <small>ID: {incident.get('id', 'N/A')} | Resolved: {incident.get('resolved_at', 'Unknown')}</small><br>
                            <em>{incident.get('description', 'No description available')}</em>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No resolved incidents to display.")
        
        with tab3:
            # Full incident table
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("🔍 No incidents detected. The system is monitoring for any issues.")
        st.markdown("""
        **Incident monitoring includes:**
        - 🎯 Pricing anomalies
        - 📊 Demand fluctuations  
        - 🚨 System performance issues
        - 🔄 Data collection failures
        - ⚡ API response delays
        """)

else:
    st.warning("⚠️ Alerts service not available. Ensure core/agents/alert_service exists and dependencies are installed.")
    st.info("When the alerts service is running, you'll see real-time incident monitoring here.")

st.markdown("---")

# =============================
# 🔎 Activity Feed (High-Level)
# =============================
st.subheader("🧠 System Activity Feed")
st.markdown("*Real-time view of all system operations and agent activities*")

try:
    from core.agents.agent_sdk.activity_log import activity_log
    items = activity_log.recent(100)  # Get more items for activity page
    
    if not items:
        st.info("🔍 No recent activity detected. Ask a pricing question in the AI Assistant to see system activity here.")
    else:
        # Activity filter controls
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Filter by Status:",
                ["All", "completed", "in_progress", "failed", "info"],
                index=0
            )
        with col2:
            agent_filter = st.selectbox(
                "Filter by Agent:",
                ["All"] + list(set(ev.get('agent', 'Unknown') for ev in items)),
                index=0
            )
        with col3:
            if st.button("🔄 Refresh Activity", use_container_width=True):
                st.rerun()
        
        # Filter items based on selection
        filtered_items = items
        if status_filter != "All":
            filtered_items = [ev for ev in filtered_items if ev.get("status") == status_filter]
        if agent_filter != "All":
            filtered_items = [ev for ev in filtered_items if ev.get("agent") == agent_filter]
        
        st.markdown(f"**Showing {len(filtered_items)} of {len(items)} activities**")
        
        # Display activities
        for i, ev in enumerate(filtered_items):
            status = ev.get("status", "info")
            agent = ev.get("agent", "Unknown")
            action = ev.get("action", "Unknown action")
            timestamp = ev.get("ts", "Unknown time")
            message = ev.get("message", "")
            
            # Status badge
            if status == "completed":
                badge = "🟢"
                status_text = "Completed"
            elif status == "in_progress":
                badge = "🟡"
                status_text = "In Progress"
            elif status == "failed":
                badge = "🔴"
                status_text = "Failed"
            else:
                badge = "🔵"
                status_text = "Info"
            
            with st.container():
                st.markdown(f"""
                <div class="activity-item">
                    <div style="display: flex; justify-content: between; align-items: center;">
                        <div>
                            <strong>{badge} {agent}</strong> — {action}
                            <br><small>🕐 {timestamp} | Status: {status_text}</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if message:
                    st.caption(f"💬 {message}")
                
                details = ev.get("details")
                if details:
                    with st.expander(f"🔍 Activity Details #{i+1}", expanded=False):
                        st.json(details)

except Exception as e:
    st.warning("⚠️ Activity feed temporarily unavailable.")
    st.info("The activity logger will appear once the agent modules are loaded and active.")
    
    # Show mock activity for demonstration
    st.markdown("### Sample Activity (Demo)")
    mock_activities = [
        {"badge": "🟢", "agent": "PricingOptimizer", "action": "Price analysis completed", "time": "14:32:15", "message": "Analyzed 5 products, identified 2 optimization opportunities"},
        {"badge": "🟡", "agent": "DataCollector", "action": "Collecting market data", "time": "14:31:45", "message": "Fetching competitor prices from 3 sources"},
        {"badge": "🔵", "agent": "UserInteraction", "action": "Processing user query", "time": "14:30:22", "message": "User asked about demand forecasting"},
        {"badge": "🟢", "agent": "AlertService", "action": "Monitoring started", "time": "14:25:10", "message": "System health checks active"},
    ]
    
    for activity in mock_activities:
        st.markdown(f"""
        <div class="activity-item">
            <strong>{activity['badge']} {activity['agent']}</strong> — {activity['action']}
            <br><small>🕐 {activity['time']}</small>
            <br><em>{activity['message']}</em>
        </div>
        """, unsafe_allow_html=True)

# ====================
# System Health Status
# ====================
st.markdown("---")
st.subheader("⚡ System Health")

# Mock system health data
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🤖 AI Agents", "4/4 Active", delta="Online")
with col2:
    st.metric("📊 Data Sources", "3/3 Connected", delta="Healthy")
with col3:
    st.metric("🔄 Background Tasks", "2 Running", delta="Normal")
with col4:
    st.metric("📡 API Status", "99.9% Uptime", delta="+0.1%")

# System services status
st.markdown("### Service Status")
services = [
    {"name": "🎯 Pricing Optimizer", "status": "🟢 Active", "last_run": "2 minutes ago"},
    {"name": "📊 Data Collector", "status": "🟢 Active", "last_run": "5 minutes ago"},
    {"name": "🤖 AI Assistant", "status": "🟢 Active", "last_run": "1 minute ago"},
    {"name": "🔔 Alert Service", "status": "🟡 Starting", "last_run": "10 minutes ago"},
    {"name": "📈 Analytics Engine", "status": "🟢 Active", "last_run": "3 minutes ago"},
]

for service in services:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write(service["name"])
    with col2:
        st.write(service["status"])
    with col3:
        st.write(service["last_run"])

# ====================
# Activity Export
# ====================
st.markdown("---")
if st.button("📤 Export Activity Log"):
    try:
        from core.agents.agent_sdk.activity_log import activity_log
        items = activity_log.recent(500)  # Get more items for export
        
        if items:
            activity_text = "ACTIVITY LOG EXPORT\n" + "="*50 + "\n\n"
            for ev in items:
                activity_text += f"[{ev.get('ts')}] {ev.get('agent')} - {ev.get('action')}\n"
                activity_text += f"Status: {ev.get('status')}\n"
                if ev.get('message'):
                    activity_text += f"Message: {ev.get('message')}\n"
                activity_text += "-" * 30 + "\n\n"
            
            st.download_button(
                label="💾 Download Activity Log",
                data=activity_text,
                file_name=f"activity_log_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        else:
            st.info("No activity data available to export.")
    except Exception:
        st.info("Activity export feature will be available when the activity logger is active.")