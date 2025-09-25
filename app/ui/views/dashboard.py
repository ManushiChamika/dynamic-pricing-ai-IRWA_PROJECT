from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime, timedelta

from app.ui.state.session import user_display_name
from app.ui.theme.inject import apply_theme
from app.ui.services.activity import recent as recent_activity


def view() -> None:
    apply_theme(False)

    st.markdown(f"## 👋 Welcome, **{user_display_name()}**")

    # KPI tiles (placeholder logic; replace with real metrics when available)
    total_sales = random.randint(100_000, 200_000)
    avg_price = random.uniform(20, 40)
    units_sold = random.randint(5_000, 15_000)

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Sales", f"${total_sales:,.0f}", "+3.4%")
    c2.metric("💵 Avg. Price", f"${avg_price:,.2f}", "-1.2%")
    c3.metric("📦 Units Sold", f"{units_sold:,}", "+6.3%")

    st.markdown("---")

    # Charts (placeholder data)
    df = pd.DataFrame({
        "Date": pd.date_range(datetime.now() - timedelta(days=60), periods=30),
        "Demand": [random.randint(200, 500) for _ in range(30)],
    })
    fig = px.line(df, x="Date", y="Demand", markers=True)
    st.subheader("📈 Demand Trend")
    st.plotly_chart(fig, use_container_width=True)

    # Activity strip
    st.subheader("🧠 Recent Activity")
    items = recent_activity(10)
    if not items:
        st.info("No recent activity.")
    else:
        for ev in items:
            status = ev.get("status", "info")
            badge = "🟢" if status == "completed" else ("🟡" if status == "in_progress" else ("🔴" if status == "failed" else "🔵"))
            st.markdown(f"{badge} [{ev.get('ts')}] **{ev.get('agent')}** — {ev.get('action')}")
            msg = ev.get("message")
            if msg:
                st.caption(msg)
