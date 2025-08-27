import streamlit as st
import plotly.express as px
import pandas as pd
import random
import os
import json
from datetime import datetime

from core.agents.user_interaction_agent import UserInteractionAgent

# ---- Streamlit Page Config ----
st.set_page_config(page_title="Dynamic Pricing Dashboard", page_icon="📊", layout="wide")

# ---- Custom CSS ----
st.markdown("""
<style>
.stApp { background-color: #a6bdde; color: #000000; }
.stMetric { background-color: #7da3c3; border-radius: 10px; padding: 10px; color: #000000; }
.stSidebar { background-color: #7da3c3; color: #000000; }
.stChatMessage { background-color: #6b92b1; color: #000000; border-radius: 10px; padding: 5px; }
.stTextInput > div > div > input { background-color: #a6bdde; color: #000000; border: 1px solid #000000; }
</style>
""", unsafe_allow_html=True)

# ---- Simulated Data ----
def get_dynamic_pricing_data():
    products = ["A", "B", "C", "D", "E"]
    data = []
    for p in products:
        price = random.randint(100, 200)
        demand = random.randint(150, 500)
        data.append({"Product": p, "Price": price, "Demand": demand})
    return pd.DataFrame(data)

def get_demand_trend():
    return pd.DataFrame({
        "Date": pd.date_range(start="2025-01-01", periods=12, freq="M"),
        "Demand": [random.randint(200, 400) for _ in range(12)]
    })

# ---- User Data Persistence ----
DATA_FILE = "user_data.json"

def load_user_data(email):
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                all_data = json.load(f)
            return all_data.get(email, {"chat_history": [], "metrics": None})
        except json.JSONDecodeError:
            return {"chat_history": [], "metrics": None}
    return {"chat_history": [], "metrics": None}

def save_user_data(email, data):
    all_data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            all_data = {}
    all_data[email] = data
    with open(DATA_FILE, "w") as f:
        json.dump(all_data, f, indent=4)

# ---- Session Check ----
if "session" not in st.session_state or st.session_state["session"] is None:
    st.warning("⚠️ You must log in first!")
    st.stop()

user_session = st.session_state["session"]
user_name = user_session.get("full_name", "User")
user_email = user_session.get("email")

# ---- Load Previous Data ----
user_data = load_user_data(user_email)
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = user_data.get("chat_history", [])
if "metrics" not in st.session_state:
    st.session_state["metrics"] = user_data.get("metrics", None)

# ---- Initialize Local Agent ----
agent = UserInteractionAgent(user_name=user_name, model_name="gpt2")  # or smaller chat model

# ---- Dashboard Header ----
st.markdown(f"<h2 style='color:#000000;'>👋 Welcome back, <b>{user_name}</b></h2>", unsafe_allow_html=True)

# ---- Metrics ----
st.subheader("📈 Key Business Metrics")
df = get_dynamic_pricing_data()
col1, col2, col3 = st.columns(3)

total_sales = int(df['Price'].sum() * 1000)
avg_price = float(df['Price'].mean())
units_sold = int(df['Demand'].sum())

if st.session_state["metrics"] is None:
    st.session_state["metrics"] = {
        "total_sales": total_sales,
        "avg_price": avg_price,
        "units_sold": units_sold
    }

col1.metric(label="💰 Total Sales", value=f"${st.session_state['metrics']['total_sales']:,}", delta="+5%")
col2.metric(label="💵 Avg. Price", value=f"${st.session_state['metrics']['avg_price']:.2f}", delta="-2%")
col3.metric(label="📦 Units Sold", value=f"{st.session_state['metrics']['units_sold']:,}", delta="+8%")
st.markdown("---")

save_user_data(user_email, {
    "chat_history": st.session_state["chat_history"],
    "metrics": st.session_state["metrics"]
})

# ---- Charts ----
st.subheader("📊 AI Prediction: Price vs Demand")
fig = px.scatter(
    df, x="Price", y="Demand", size="Demand", color="Product",
    hover_name="Product", template="plotly_white", width=900, height=500
)
fig.update_layout(plot_bgcolor="#5896ed", paper_bgcolor="#5896ed", font_color="#000000")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📈 AI Forecast: Demand Over Time")
trend_df = get_demand_trend()
fig2 = px.line(trend_df, x="Date", y="Demand", markers=True, template="plotly_white", width=900, height=400)
fig2.update_traces(line=dict(color="#FFFFFF"))
fig2.update_layout(plot_bgcolor="#5896ed", paper_bgcolor="#5896ed", font_color="#000000")
st.plotly_chart(fig2, use_container_width=True)

# ---- Sidebar ----
st.sidebar.title("⚙️ Menu")
st.sidebar.subheader("👤 User Info")
st.sidebar.info(f"**Name:** {user_name}\n**Email:** {user_email}")

# Chat history
st.sidebar.subheader("💬 Chat History")
chat_container = st.sidebar.container()
for chat in st.session_state.chat_history:
    role = chat.get("role")
    message = chat.get("content")
    time = chat.get("time", datetime.now().strftime("%H:%M:%S"))
    if role == "user":
        chat_container.markdown(f"🧑 **[{time}] User:** {message}")
    else:
        chat_container.markdown(f"🤖 **[{time}] Bot:** {message}")

# Chat input
if user_input := st.chat_input("Ask me about pricing, demand, or sales..."):
    st.session_state["chat_history"].append({
        "role": "user",
        "content": user_input,
        "time": datetime.now().strftime("%H:%M:%S")
    })
    with st.chat_message("user"):
        st.markdown(user_input)

    response = agent.get_response(user_input)
    st.session_state["chat_history"].append({
        "role": "assistant",
        "content": response,
        "time": datetime.now().strftime("%H:%M:%S")
    })
    with st.chat_message("assistant"):
        st.markdown(response)

    save_user_data(user_email, {
        "chat_history": st.session_state["chat_history"],
        "metrics": st.session_state["metrics"]
    })

# Logout
if st.sidebar.button("🚪 Logout"):
    st.session_state["session"] = None
    st.success("You have been logged out. Please refresh or go back to login.")
    st.stop()
