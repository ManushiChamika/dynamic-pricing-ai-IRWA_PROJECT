
"""
Dynamic Pricing Dashboard (safe + fast)
- No heavy model loads at page import
- Works offline; optional chat agent is lazy-loaded
"""
from __future__ import annotations
import os, random
import pandas as pd
import plotly.express as px
import streamlit as st

# In multipage apps, set_page_config may already be called in the main app.
# Avoid crashing the page with a duplicate call.
try:
    st.set_page_config(page_title="Dynamic Pricing Dashboard", page_icon="📊", layout="wide")
except Exception:
    pass
# Keep styling minimal and theme-friendly (no forced colors that can hide content).


def get_dynamic_pricing_data() -> pd.DataFrame:
    products = ["A", "B", "C", "D", "E"]
    data = []
    for p in products:
        price = random.randint(100, 200)
        demand = random.randint(150, 500)
        data.append({"Product": p, "Price": price, "Demand": demand})
    return pd.DataFrame(data)

def get_demand_trend() -> pd.DataFrame:
    return pd.DataFrame({
        "Date": pd.date_range(start="2025-01-01", periods=12, freq="M"),
        "Demand": [random.randint(200, 400) for _ in range(12)]
    })

class StubAgent:
    def __init__(self, user_name: str = "User", model_name: str = "stub"):
        self.user_name = user_name
        self.model_name = model_name
    def get_response(self, text: str) -> str:
        t = (text or "").lower()
        if "price" in t:
            return "💡 Suggestion: adjust prices using demand trends and competitor gaps."
        if "demand" in t:
            return "📊 Demand is rising; watch seasonal patterns and stock levels."
        return f"👋 Hi {self.user_name}! Ask about price, demand, or sales."

@st.cache_resource(show_spinner=False)
def load_chat_agent(user_name: str):
    # Default to stub unless explicitly overridden
    if os.getenv("UI_AGENT", "stub").lower() == "stub":
        return StubAgent(user_name)
    try:
        # Align with repo structure: core.agents.user_interact_agent.UserInteractAgent
        from core.agents.user_interact_agent import UserInteractAgent  # type: ignore
        model = os.getenv("UI_AGENT_MODEL", "distilgpt2")
        return UserInteractAgent(product_name="SKU-123")  # uses internal pricing brain
    except Exception as e:
        st.sidebar.warning(f"Using stub chat agent ({e})")
        return StubAgent(user_name)

# ---- Session guard (demo-friendly) ----
if "session" not in st.session_state or st.session_state.get("session") is None:
    demo_mode = True
    user_session = {"full_name": "Demo User", "email": "demo@example.com"}
    st.info("ℹ️ Demo mode: you are not logged in. Showing sample data.")
else:
    demo_mode = False
    user_session = st.session_state["session"]

user_name = user_session.get("full_name", "User")
user_email = user_session.get("email") or "anonymous@example.com"

st.markdown(f"<h2 style='color:#000;'>👋 Welcome back, <b>{user_name}</b></h2>", unsafe_allow_html=True)

st.subheader("📈 Key Business Metrics")
df = get_dynamic_pricing_data()
total_sales = int((df["Price"] * df["Demand"]).sum())
avg_price = float(df["Price"].mean())
units_sold = int(df["Demand"].sum())

col1, col2, col3 = st.columns(3)
col1.metric(label="💰 Total Sales", value=f"${total_sales:,}", delta="+5%")
col2.metric(label="💵 Avg. Price", value=f"${avg_price:.2f}", delta="-2%")
col3.metric(label="📦 Units Sold", value=f"{units_sold:,}", delta="+8%")
st.markdown("---")

st.subheader("📊 AI Prediction: Price vs Demand")
theme_base = st.get_option("theme.base") if hasattr(st, "get_option") else "light"
tpl = "plotly_dark" if theme_base == "dark" else "plotly_white"
fig = px.scatter(
    df, x="Price", y="Demand", size="Demand", color="Product",
    hover_name="Product", template=tpl, width=900, height=500
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("📈 AI Forecast: Demand Over Time")
trend_df = get_demand_trend()
fig2 = px.line(trend_df, x="Date", y="Demand", markers=True,
               template=tpl, width=900, height=400)
st.plotly_chart(fig2, use_container_width=True)

tab1, tab2 = st.tabs(["📊 Charts", "💬 AI Chat Assistant"])
with tab2:
    st.session_state.setdefault("chat_history", [])
    for m in st.session_state["chat_history"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    user_input = st.chat_input("Ask me about pricing, demand, or sales…")
    if user_input:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        agent = load_chat_agent(user_name)  # lazy
        reply = agent.get_response(user_input)
        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
