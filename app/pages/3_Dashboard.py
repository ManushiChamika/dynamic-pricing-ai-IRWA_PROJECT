import streamlit as st
import pandas as pd
import random
import os
import json
from datetime import datetime
import sys
import pathlib

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
    # Extract part before @ from email
    user_name = user_email.split("@")[0]

# ---- Streamlit Page Config ----
st.set_page_config(page_title="Dashboard - FluxPricer AI", page_icon="📊", layout="wide")

# ---- Custom CSS ----
st.markdown("""
<style>
.stApp { background-color: #a6bdde; color: #000000; }
.stMetric { background-color: #7da3c3; border-radius: 10px; padding: 10px; color: #000000; }
.stSidebar { background-color: #7da3c3; color: #000000; }
</style>
""", unsafe_allow_html=True)

# ====================
# Simulated Data Layer
# ====================
def get_dynamic_pricing_data() -> pd.DataFrame:
    products = ["A", "B", "C", "D", "E"]
    data = []
    for p in products:
        price = random.randint(100, 200)
        demand = random.randint(150, 500)
        data.append({"Product": p, "Price": price, "Demand": demand})
    return pd.DataFrame(data)

# ==========================
# Simple User Data Persistence
# ==========================
DATA_FILE = "user_data.json"

def load_user_data(email: str):
    """Load user data."""
    empty = {"metrics": None}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                all_data = json.load(f)
            user = all_data.get(email)
            if not user:
                return empty
            return {"metrics": user.get("metrics")}
        except json.JSONDecodeError:
            return empty
    return empty

def save_user_data(email: str, data: dict):
    """Save user data."""
    all_data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            all_data = {}

    payload = {"metrics": data.get("metrics")}
    all_data[email] = payload
    with open(DATA_FILE, "w") as f:
        json.dump(all_data, f, indent=4)

# Load persisted user data
if "metrics" not in st.session_state:
    _loaded = load_user_data(user_email)
    st.session_state.setdefault("metrics", _loaded.get("metrics", None))

# ===================
# Dashboard Header/UI
# ===================
st.markdown(f"<h1 style='color:#000000;'>🏠 Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color:#000000;'>Welcome back, <b>{user_name}</b></h3>", unsafe_allow_html=True)

# Navigation
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.button("🏠 Dashboard", disabled=True, use_container_width=True)
with col2:
    if st.button("📊 Analytics", use_container_width=True):
        st.switch_page("pages/4_Analytics.py")
with col3:
    if st.button("🤖 AI Assistant", use_container_width=True):
        st.switch_page("pages/5_AI_Assistant.py")
with col4:
    if st.button("📋 Activity", use_container_width=True):
        st.switch_page("pages/6_Activity.py")

st.markdown("---")

# ---- Quick Actions ----
st.subheader("🚀 Quick Actions")
action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    if st.button("📈 View Analytics", key="quick_analytics", use_container_width=True):
        st.switch_page("pages/4_Analytics.py")

with action_col2:
    if st.button("🤖 Ask AI", key="quick_ai", use_container_width=True):
        st.switch_page("pages/5_AI_Assistant.py")

with action_col3:
    if st.button("🔔 Check Activity", key="quick_activity", use_container_width=True):
        st.switch_page("pages/6_Activity.py")

with action_col4:
    if st.button("👤 Profile", key="quick_profile", use_container_width=True):
        st.switch_page("pages/4_Profile.py")

st.markdown("---")

# ---- Key Metrics ----
st.subheader("📈 Key Business Metrics")
df = get_dynamic_pricing_data()

# Example business metrics (revenue = sum of price*demand for this random snapshot)
total_sales = int((df["Price"] * df["Demand"]).sum())
avg_price = float(df["Price"].mean())
units_sold = int(df["Demand"].sum())

if st.session_state["metrics"] is None:
    st.session_state["metrics"] = {
        "total_sales": total_sales,
        "avg_price": avg_price,
        "units_sold": units_sold
    }

col1, col2, col3 = st.columns(3)
col1.metric(label="💰 Total Sales", value=f"${st.session_state['metrics']['total_sales']:,}", delta="+5%")
col2.metric(label="💵 Avg. Price", value=f"${st.session_state['metrics']['avg_price']:.2f}", delta="-2%")
col3.metric(label="📦 Units Sold", value=f"{st.session_state['metrics']['units_sold']:,}", delta="+8%")

# Persist metrics
save_user_data(user_email, {"metrics": st.session_state["metrics"]})

st.markdown("---")

# ---- Recent Activity Summary ----
st.subheader("🕒 Recent Activity")
try:
    from core.agents.agent_sdk.activity_log import activity_log
    items = activity_log.recent(5)  # Just show last 5 items
    if not items:
        st.info("No recent activity yet. Visit AI Assistant to generate some activity.")
    else:
        for ev in items:
            status = ev.get("status", "info")
            badge = "🟢" if status == "completed" else ("🟡" if status == "in_progress" else ("🔴" if status == "failed" else "🔵"))
            st.markdown(f"{badge} **{ev.get('agent')}** — {ev.get('action')} *({ev.get('ts')})*")
        
        if st.button("View Full Activity Feed →", key="full_activity"):
            st.switch_page("pages/6_Activity.py")
except Exception:
    st.info("Activity tracking will appear once you interact with the AI Assistant.")

st.markdown("---")

# ---- Quick Stats ----
st.subheader("📊 System Status")
status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    st.metric("🤖 Active Agents", "4", "All Online")

with status_col2:
    st.metric("🔔 Open Alerts", "2", "+1 New")

with status_col3:
    st.metric("📊 Data Points", "1.2K", "+156 Today")

with status_col4:
    st.metric("⚡ Response Time", "0.8s", "Normal")

# ---- Logout Button ----
st.markdown("---")
if st.button("🚪 Logout", key="dashboard_logout"):
    st.session_state["session"] = None
    st.success("You have been logged out.")
    st.switch_page("pages/0_Home.py")