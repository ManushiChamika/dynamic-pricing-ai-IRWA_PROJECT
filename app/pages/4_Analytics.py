import streamlit as st
import plotly.express as px
import pandas as pd
import random
import os
import json

# ---- Page Config ----
st.set_page_config(page_title="Analytics - Dynamic Pricing", page_icon="📊", layout="wide")

# ---- Custom CSS ----
st.markdown("""
<style>
.stApp { background-color: #a6bdde; color: #000000; }
.stMetric { background-color: #7da3c3; border-radius: 10px; padding: 10px; color: #000000; }
.stSidebar { background-color: #7da3c3; color: #000000; }
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
# Data Functions
# ====================
def get_dynamic_pricing_data() -> pd.DataFrame:
    """Generate simulated pricing data"""
    products = ["A", "B", "C", "D", "E"]
    data = []
    for p in products:
        price = random.randint(100, 200)
        demand = random.randint(150, 500)
        data.append({"Product": p, "Price": price, "Demand": demand})
    return pd.DataFrame(data)

def get_demand_trend() -> pd.DataFrame:
    """Generate simulated demand trend data"""
    return pd.DataFrame({
        "Date": pd.date_range(start="2025-01-01", periods=12, freq="ME"),
        "Demand": [random.randint(200, 400) for _ in range(12)]
    })

def get_extended_pricing_data() -> pd.DataFrame:
    """Generate extended pricing analytics data"""
    products = ["Product A", "Product B", "Product C", "Product D", "Product E"]
    categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]
    data = []
    for i, (p, c) in enumerate(zip(products, categories)):
        base_price = 100 + i * 20
        current_price = base_price + random.randint(-20, 30)
        competitor_price = current_price + random.randint(-15, 25)
        demand = random.randint(100, 400)
        margin = random.uniform(0.15, 0.35)
        data.append({
            "Product": p,
            "Category": c,
            "Current_Price": current_price,
            "Competitor_Price": competitor_price,
            "Demand": demand,
            "Margin": margin,
            "Revenue": current_price * demand
        })
    return pd.DataFrame(data)

# ====================
# Page Header
# ====================
st.markdown(f"<h1 style='color:#000000;'>📊 Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color:#000000;'>Welcome back, <b>{user_name}</b></h3>", unsafe_allow_html=True)

# Navigation
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/3_Dashboard.py")
with col2:
    st.button("📊 Analytics", disabled=True, use_container_width=True)
with col3:
    if st.button("🤖 AI Assistant", use_container_width=True):
        st.switch_page("pages/5_AI_Assistant.py")
with col4:
    if st.button("📋 Activity", use_container_width=True):
        st.switch_page("pages/6_Activity.py")

st.markdown("---")

# ====================
# Analytics Content
# ====================

# Get data
df = get_dynamic_pricing_data()
trend_df = get_demand_trend()
extended_df = get_extended_pricing_data()

# ---- Key Metrics Summary ----
st.subheader("📈 Key Performance Indicators")

total_revenue = int(extended_df["Revenue"].sum())
avg_margin = float(extended_df["Margin"].mean())
total_demand = int(extended_df["Demand"].sum())
avg_price = float(extended_df["Current_Price"].mean())

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 Total Revenue", f"${total_revenue:,}", delta="+12%")
with col2:
    st.metric("📊 Avg. Margin", f"{avg_margin:.1%}", delta="+2.3%")
with col3:
    st.metric("📦 Total Demand", f"{total_demand:,}", delta="+8%")
with col4:
    st.metric("💵 Avg. Price", f"${avg_price:.2f}", delta="-1.5%")

st.markdown("---")

# ---- Price vs Demand Analysis ----
st.subheader("🎯 AI Prediction: Price vs Demand Analysis")
st.markdown("*Real-time analysis of pricing impact on customer demand*")

fig1 = px.scatter(
    df, x="Price", y="Demand", size="Demand", color="Product",
    hover_name="Product", template="plotly_white",
    title="Price-Demand Correlation by Product"
)
fig1.update_layout(
    plot_bgcolor="#5896ed", 
    paper_bgcolor="#5896ed", 
    font_color="#000000",
    height=500
)
st.plotly_chart(fig1, use_container_width=True)

# ---- Demand Forecast ----
st.subheader("📈 AI Forecast: Demand Trends")
st.markdown("*12-month demand prediction using advanced ML models*")

fig2 = px.line(
    trend_df, x="Date", y="Demand", markers=True, 
    template="plotly_white",
    title="Predicted Demand Trend (Next 12 Months)"
)
fig2.update_traces(line=dict(color="#FFFFFF", width=3))
fig2.update_layout(
    plot_bgcolor="#5896ed", 
    paper_bgcolor="#5896ed", 
    font_color="#000000",
    height=400
)
st.plotly_chart(fig2, use_container_width=True)

# ---- Competitive Analysis ----
st.subheader("🏆 Competitive Pricing Analysis")

col1, col2 = st.columns(2)

with col1:
    fig3 = px.bar(
        extended_df, x="Product", y=["Current_Price", "Competitor_Price"],
        title="Price Comparison vs Competitors",
        barmode="group",
        color_discrete_map={"Current_Price": "#7da3c3", "Competitor_Price": "#ff7f7f"}
    )
    fig3.update_layout(
        plot_bgcolor="#5896ed", 
        paper_bgcolor="#5896ed", 
        font_color="#000000",
        height=400
    )
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    fig4 = px.pie(
        extended_df, values="Revenue", names="Category",
        title="Revenue Distribution by Category"
    )
    fig4.update_layout(
        plot_bgcolor="#5896ed", 
        paper_bgcolor="#5896ed", 
        font_color="#000000",
        height=400
    )
    st.plotly_chart(fig4, use_container_width=True)

# ---- Margin Analysis ----
st.subheader("💹 Profitability Analysis")

fig5 = px.scatter(
    extended_df, x="Current_Price", y="Margin", size="Revenue", 
    color="Category", hover_name="Product",
    title="Price vs Margin Analysis (Bubble size = Revenue)"
)
fig5.update_layout(
    plot_bgcolor="#5896ed", 
    paper_bgcolor="#5896ed", 
    font_color="#000000",
    height=500
)
st.plotly_chart(fig5, use_container_width=True)

# ---- Detailed Data Table ----
st.subheader("📋 Detailed Analytics Data")
st.markdown("*Complete dataset with all metrics*")

# Format the dataframe for better display
display_df = extended_df.copy()
display_df["Current_Price"] = display_df["Current_Price"].apply(lambda x: f"${x:.2f}")
display_df["Competitor_Price"] = display_df["Competitor_Price"].apply(lambda x: f"${x:.2f}")
display_df["Revenue"] = display_df["Revenue"].apply(lambda x: f"${x:,.0f}")
display_df["Margin"] = display_df["Margin"].apply(lambda x: f"{x:.1%}")

st.dataframe(display_df, use_container_width=True)

# ---- AI Insights ----
st.subheader("🧠 AI-Generated Insights")
insights = [
    "📈 Product A shows optimal price-demand balance with highest revenue potential",
    "⚠️ Product C is priced 15% below competitor average - consider price increase",
    "🎯 Electronics category generates 35% of total revenue despite being 20% of products",
    "📊 Margin optimization opportunity: Products D & E could support 5-8% price increases",
    "🔮 Demand forecast indicates 12% growth in Q2 2025 across all categories"
]

for insight in insights:
    st.info(insight)

# ---- Export Options ----
st.markdown("---")
st.subheader("📤 Export Analytics")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📊 Export Charts as PDF", use_container_width=True):
        st.info("PDF export functionality would be implemented here")
with col2:
    if st.button("📋 Download Data as CSV", use_container_width=True):
        csv = extended_df.to_csv(index=False)
        st.download_button(
            label="💾 Download CSV",
            data=csv,
            file_name="analytics_data.csv",
            mime="text/csv"
        )
with col3:
    if st.button("📧 Email Report", use_container_width=True):
        st.info("Email report functionality would be implemented here")