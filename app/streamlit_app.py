# app/streamlit_app.py  (router/bootstrap)
from queue import SimpleQueue
ALERT_QUEUE = SimpleQueue()

# 0) Make the repo root importable BEFORE any project imports or Streamlit calls
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[1]  # points to <project-root>
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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

# Optional login gating via env var UI_REQUIRE_LOGIN
import os
if os.getenv("UI_REQUIRE_LOGIN", "0").strip().lower() in {"1", "true", "yes", "on"}:
    from app.ui.state.session import require_session
    require_session()

# 5) Start the alert service once (schedule onto background loop)
if "_alerts_started" not in st.session_state:
    loop = _ensure_bg_loop()
    asyncio.run_coroutine_threadsafe(alerts.start(), loop)
    st.session_state["_alerts_started"] = True

# 6) URL-based routing for Landing vs Dashboard
from app.ui.theme.inject import apply_theme
from app.ui.services.activity import ensure_bus_bridge
from app.ui.views import dashboard as v_dashboard
from app.ui.views import incidents as v_incidents
from app.ui.views import activity_view as v_activity
from app.ui.views import rules as v_rules
from app.ui.views import settings as v_settings
from app.ui.views import landing as v_landing

# Check URL parameters for page routing
page = st.query_params.get("page", "landing")  # Default to landing page
section_param = st.query_params.get("section", None)

# Landing Page - Separate URL and Layout
if page == "landing":
    v_landing.view()
    st.stop()  # Don't render dashboard navigation

# Dashboard Mode - Full App Interface
# Apply modern light theme
apply_theme(False)

try:
    ensure_bus_bridge()
except Exception:
    pass

# Modern Navigation System with Enhanced Styling
st.sidebar.markdown("---")

# Initialize current section in session state
if 'current_section' not in st.session_state:
    st.session_state.current_section = "AI CHAT"

# Handle redirects and force navigation
if st.session_state.get('redirect_to_chat', False) or st.session_state.get('force_chat', False) or section_param == "chat":
    st.session_state.current_section = "AI CHAT"
    st.session_state['redirect_to_chat'] = False
    st.session_state['force_chat'] = False

# Enhanced CSS for professional navigation
st.sidebar.markdown("""
<style>
/* Custom Navigation Styles */
.stButton > button {
    width: 100% !important;
    margin: 0.25rem 0 !important;
    padding: 0.75rem 1rem !important;
    border-radius: 0.5rem !important;
    text-align: left !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    border: 1px solid #E2E8F0 !important;
    background: #F8FAFC !important;
    color: #64748B !important;
}

.stButton > button:hover {
    background: #F1F5F9 !important;
    border-color: #CBD5E1 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

.nav-header {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 1rem 0 0.5rem 0;
    padding: 0 0.5rem;
}

.nav-active {
    background: linear-gradient(135deg, #3B82F6, #1D4ED8) !important;
    color: white !important;
    border-color: #3B82F6 !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
}

.nav-active:hover {
    background: linear-gradient(135deg, #1D4ED8, #1E40AF) !important;
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
}

.quick-chat-btn {
    background: linear-gradient(135deg, #10B981, #059669) !important;
    color: white !important;
    border-color: #10B981 !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
}

.quick-chat-btn:hover {
    background: linear-gradient(135deg, #059669, #047857) !important;
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)

# AI Assistant Section
st.sidebar.markdown('<div class="nav-header">🤖 AI Assistant</div>', unsafe_allow_html=True)

# Quick Chat Button with special styling
quick_chat_clicked = st.sidebar.button("💬 **Quick Chat**", key="quick_chat", use_container_width=True)
if quick_chat_clicked:
    st.session_state.current_section = "AI CHAT"
    st.rerun()

# Add special styling for Quick Chat button
st.sidebar.markdown("""
<style>
button[key="quick_chat"] {
    background: linear-gradient(135deg, #10B981, #059669) !important;
    color: white !important;
    border-color: #10B981 !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
}
button[key="quick_chat"]:hover {
    background: linear-gradient(135deg, #059669, #047857) !important;
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown('<div style="font-size: 0.75rem; color: #64748B; text-align: center; margin-bottom: 1rem; font-style: italic;">Ask anything: pricing, analysis, optimization...</div>', unsafe_allow_html=True)

# Navigation items configuration
nav_items = [
    {"key": "AI CHAT", "icon": "🤖", "label": "AI Chat"},
    {"key": "HOME", "icon": "🏠", "label": "Home"},
    {"key": "PRICING", "icon": "💰", "label": "Pricing"},
    {"key": "ANALYTICS", "icon": "📊", "label": "Analytics"},
    {"key": "OPERATIONS", "icon": "⚡", "label": "Operations"},
    {"key": "SETTINGS", "icon": "⚙️", "label": "Settings"}
]

# Main Navigation Section
st.sidebar.markdown('<div class="nav-header">Navigation</div>', unsafe_allow_html=True)

# Create navigation buttons with active states
for item in nav_items:
    is_active = st.session_state.current_section == item["key"]
    button_key = f"nav_{item['key']}"
    button_label = f"{item['icon']} **{item['label']}**" if is_active else f"{item['icon']} {item['label']}"
    
    # Create button with conditional styling
    nav_clicked = st.sidebar.button(button_label, key=button_key, use_container_width=True)
    
    # Apply active styling if this is the current section
    if is_active:
        st.sidebar.markdown(f"""
        <style>
        button[key="{button_key}"] {{
            background: linear-gradient(135deg, #3B82F6, #1D4ED8) !important;
            color: white !important;
            border-color: #3B82F6 !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
            font-weight: 600 !important;
        }}
        button[key="{button_key}"]:hover {{
            background: linear-gradient(135deg, #1D4ED8, #1E40AF) !important;
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    
    if nav_clicked:
        st.session_state.current_section = item["key"]
        st.rerun()

# Get the selected section for routing
section = f"🤖 {st.session_state.current_section}" if st.session_state.current_section == "AI CHAT" else f"🏠 {st.session_state.current_section}"

# Back to Landing Section
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="nav-header">Quick Actions</div>', unsafe_allow_html=True)

back_clicked = st.sidebar.button("🏠 **← Back to Landing**", use_container_width=True)
if back_clicked:
    st.query_params.clear()
    st.rerun()

# Route to appropriate views - Chat First!
if section == "🤖 AI CHAT":
    # Primary AI Chat Interface - The Core Product Feature
    from app.ui.views import chat as v_chat
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #3B82F6;">🤖 FluxPricer AI Assistant</h2>
        <p style="color: #64748B;">Interact with our multi-agent system using natural language</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add helpful prompt suggestions
    st.markdown("### 💡 **Try asking:**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 **Analyze current pricing trends**", use_container_width=True):
            st.session_state['chat_input'] = "Analyze current pricing trends for all products"
        if st.button("💰 **Optimize prices for Product X**", use_container_width=True):
            st.session_state['chat_input'] = "Optimize prices for Product X based on market data"
        if st.button("📊 **Show revenue performance**", use_container_width=True):
            st.session_state['chat_input'] = "Show me the revenue performance for this month"
            
    with col2:
        if st.button("⚡ **Set up auto-pricing rules**", use_container_width=True):
            st.session_state['chat_input'] = "Help me set up automated pricing rules"
        if st.button("🚨 **Check system alerts**", use_container_width=True):
            st.session_state['chat_input'] = "What alerts do I need to review?"
        if st.button("📈 **Generate pricing report**", use_container_width=True):
            st.session_state['chat_input'] = "Generate a comprehensive pricing analysis report"
    
    st.markdown("---")
    
    # Main chat interface
    v_chat.view()
    
elif section == "🏠 HOME":
    # Control Center Dashboard - overview of all systems
    v_dashboard.view()
elif section == "💰 PRICING":
    # Pricing workflow: AI-powered optimization
    from app.ui.views import chat as v_chat
    st.subheader("💰 AI-Powered Pricing Optimization")
    
    # Sub-navigation for pricing workflow - Chat-centric
    pricing_tab = st.radio(
        "Pricing Section",
        ["🤖 AI Chat & Optimization", "📈 Price Analysis", "📋 Proposals", "⚡ Auto-Apply"],
        horizontal=True
    )
    
    if pricing_tab == "🤖 AI Chat & Optimization":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <h4 style="margin: 0; color: white;">💬 Chat with AI for Pricing Optimization</h4>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Ask questions, get recommendations, and optimize prices using natural language</p>
        </div>
        """, unsafe_allow_html=True)
        v_chat.view()  # Main AI chat interface
    elif pricing_tab == "📈 Price Analysis":
        st.info("📈 Price Analysis - Market data and pricing trends")
        st.markdown("**Coming Soon**: Use AI Chat to ask '*Show me price analysis for Product X*'")
        # TODO: Implement price analysis view
    elif pricing_tab == "📋 Proposals":
        st.info("📋 Pricing Proposals - Review and manage price changes")
        st.markdown("**Coming Soon**: Use AI Chat to ask '*Show me pending pricing proposals*'")
        # TODO: Implement proposals view
    elif pricing_tab == "⚡ Auto-Apply":
        st.info("⚡ Auto-Apply Settings - Automated pricing rules")
        st.markdown("**Coming Soon**: Use AI Chat to ask '*Help me set up auto-pricing rules*'")
        # TODO: Implement auto-apply view
        
elif section == "📊 ANALYTICS":
    # Business Intelligence and reporting
    st.subheader("📊 Business Analytics")
    analytics_tab = st.radio(
        "Analytics Section",
        ["📈 Performance", "💹 Market Trends", "📊 Reports"],
        horizontal=True
    )
    
    if analytics_tab == "📈 Performance":
        st.info("📈 Performance metrics and KPIs")
        v_dashboard.view()  # Reuse dashboard for now
    elif analytics_tab == "💹 Market Trends":
        st.info("💹 Market analysis and competitor insights")
        # TODO: Implement market trends view
    elif analytics_tab == "📊 Reports":
        st.info("📊 Custom reports and data exports")
        # TODO: Implement reports view
        
elif section == "⚡ OPERATIONS":
    # Monitoring, alerts, and system health
    st.subheader("⚡ Operations Center")
    ops_tab = st.radio(
        "Operations Section", 
        ["🚨 Alerts", "📋 Activity", "🔧 Rules", "🏥 Health"],
        horizontal=True
    )
    
    if ops_tab == "🚨 Alerts":
        v_incidents.view()
    elif ops_tab == "📋 Activity":
        v_activity.view()
    elif ops_tab == "🔧 Rules":
        v_rules.view()
    elif ops_tab == "🏥 Health":
        st.info("🏥 System health monitoring")
        # TODO: Implement system health view
        
elif section == "⚙️ SETTINGS":
    # Configuration and user preferences
    v_settings.view()
