from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime, timedelta


from app.ui.theme.inject import apply_theme
from app.ui.theme.charts import apply_light_theme_to_plotly, get_chart_colors
from app.ui.services.activity import recent as recent_activity


def view() -> None:
    apply_theme(False)

    # Dashboard header - simplified for internal use
    st.markdown(f"""
    <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
        <h2 style="color: #3B82F6; margin-bottom: 0.5rem;">FluxPricer Control Center</h2>
        <p style="color: #64748B;">Welcome to FluxPricer AI • {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    """, unsafe_allow_html=True)

    # System Status Overview (Top Priority)
    st.markdown("### 🎛️ **System Status**")
    
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    
    with status_col1:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
            <div><strong>AI Optimizer</strong></div>
            <div class="badge success" style="margin-top: 0.5rem;">ACTIVE</div>
        </div>
        """, unsafe_allow_html=True)
    
    with status_col2:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
            <div><strong>Data Collector</strong></div>
            <div class="badge success" style="margin-top: 0.5rem;">RUNNING</div>
        </div>
        """, unsafe_allow_html=True)
    
    with status_col3:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🚨</div>
            <div><strong>Alert Service</strong></div>
            <div class="badge success" style="margin-top: 0.5rem;">MONITORING</div>
        </div>
        """, unsafe_allow_html=True)
        
    with status_col4:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
            <div><strong>Auto-Apply</strong></div>
            <div class="badge warning" style="margin-top: 0.5rem;">STANDBY</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Key Performance Indicators
    st.markdown("### 📊 **Key Performance Indicators**")

    # Generate realistic mock data
    total_sales = random.randint(100_000, 200_000)
    avg_price = random.uniform(20, 40)
    units_sold = random.randint(5_000, 15_000)
    active_rules = random.randint(15, 25)
    optimizations = random.randint(5, 12)
    alerts_pending = random.randint(0, 5)

    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    with kpi_col1:
        st.metric("💰 Total Revenue", f"${total_sales:,.0f}", "+3.4%")
        st.metric("📦 Units Sold", f"{units_sold:,}", "+6.3%")
        
    with kpi_col2:
        st.metric("💵 Avg. Price", f"${avg_price:,.2f}", "-1.2%")
        st.metric("🔧 Active Rules", f"{active_rules}", "+2")
        
    with kpi_col3:
        st.metric("🤖 AI Optimizations", f"{optimizations}", "+4")
        st.metric("🚨 Pending Alerts", f"{alerts_pending}", "0")

    st.markdown("---")

    # AI Assistant - Prominent Feature
    st.markdown("### 🤖 **Ask FluxPricer AI**")
    
    # Prominent chat shortcut
    st.markdown("""
    <div class="card" style="background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); color: white; text-align: center; padding: 1.5rem; margin-bottom: 1rem;">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💬</div>
        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">Chat with AI Assistant</div>
        <div style="opacity: 0.9;">Get instant insights, optimize pricing, and manage your business with natural language</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick AI prompts
    chat_col1, chat_col2 = st.columns(2)
    
    with chat_col1:
        if st.button("🤖 **'Optimize all prices'**", use_container_width=True):
            st.info("💬 Redirecting to AI Chat...")
            st.session_state['redirect_to_chat'] = True
            st.session_state['chat_prompt'] = "Optimize prices for all products based on current market conditions"
            # Maintain dashboard URL
            st.query_params["page"] = "dashboard"
            st.query_params["section"] = "chat"
            
        if st.button("📊 **'Show revenue analysis'**", use_container_width=True):
            st.info("💬 Redirecting to AI Chat...")
            st.session_state['redirect_to_chat'] = True
            st.session_state['chat_prompt'] = "Show me a detailed revenue analysis for this month"
            # Maintain dashboard URL
            st.query_params["page"] = "dashboard"
            st.query_params["section"] = "chat"
            
    with chat_col2:
        if st.button("🚨 **'What needs attention?'**", use_container_width=True):
            st.info("💬 Redirecting to AI Chat...")
            st.session_state['redirect_to_chat'] = True
            st.session_state['chat_prompt'] = "What alerts and issues need my immediate attention?"
            # Maintain dashboard URL
            st.query_params["page"] = "dashboard"
            st.query_params["section"] = "chat"
            
        if st.button("⚡ **'Set up auto-pricing'**", use_container_width=True):
            st.info("💬 Redirecting to AI Chat...")
            st.session_state['redirect_to_chat'] = True
            st.session_state['chat_prompt'] = "Help me set up automated pricing rules"
            # Maintain dashboard URL
            st.query_params["page"] = "dashboard"
            st.query_params["section"] = "chat"

    st.markdown("---")

    # Quick Actions Panel
    st.markdown("### ⚡ **Quick Actions**")
    
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("📋 **View Proposals**", use_container_width=True):
            st.info("📋 Redirecting to Pricing Proposals...")
            
    with action_col2:
        if st.button("📊 **Generate Report**", use_container_width=True):
            st.success("📊 Report generation started!")
            
    with action_col3:
        if st.button("🔧 **Manage Rules**", use_container_width=True):
            st.info("🔧 Redirecting to Operations...")
            
    with action_col4:
        if st.button("⚙️ **Settings**", use_container_width=True):
            st.info("⚙️ Opening settings...")

    st.markdown("---")

    # Business Trends (Dual Charts)
    st.markdown("### 📈 **Business Trends**")
    
    # Generate trend data
    df = pd.DataFrame({
        "Date": pd.date_range(datetime.now() - timedelta(days=30), periods=30),
        "Revenue": [random.randint(8000, 25000) for _ in range(30)],
        "Demand": [random.randint(200, 600) for _ in range(30)],
        "Price": [random.uniform(15, 45) for _ in range(30)],
    })
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Revenue trend
        colors = get_chart_colors()
        fig_revenue = px.area(df, x="Date", y="Revenue", 
                             title="📊 Daily Revenue Trend",
                             color_discrete_sequence=[colors[0]])
        fig_revenue = apply_light_theme_to_plotly(fig_revenue)
        fig_revenue.update_traces(fill='tonexty', line_width=2)
        fig_revenue.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with chart_col2:
        # Demand vs Price
        fig_scatter = px.scatter(df, x="Price", y="Demand", size="Revenue",
                               title="💹 Price vs Demand Analysis",
                               color_discrete_sequence=[colors[1]])
        fig_scatter = apply_light_theme_to_plotly(fig_scatter)
        fig_scatter.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    # Recent Activity & Alerts Side by Side
    activity_col, alerts_col = st.columns(2)
    
    with activity_col:
        st.markdown("### 🧠 **Recent Activity**")
        items = recent_activity(5)  # Limit to 5 for home view
        if not items:
            st.info("No recent activity.")
        else:
            for ev in items:
                status = ev.get("status", "info")
                # Use styled badges instead of emojis
                if status == "completed":
                    badge_class = "success"
                    icon = "✅"
                elif status == "in_progress": 
                    badge_class = "info"
                    icon = "⏳"
                elif status == "failed":
                    badge_class = "error" 
                    icon = "❌"
                else:
                    badge_class = "info"
                    icon = "ℹ️"
                
                # Create a compact activity item for home view
                st.markdown(f"""
                <div class="card" style="margin-bottom: 0.5rem; padding: 0.5rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;">
                        <span>{icon}</span>
                        <span class="badge {badge_class}" style="font-size: 0.625rem;">{status}</span>
                        <strong>{ev.get('agent', 'System')}</strong>
                        <span style="color: #64748B;">—</span>
                        <span>{ev.get('action', 'Unknown action')[:30]}...</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with alerts_col:
        st.markdown("### 🚨 **System Alerts**")
        # Mock alerts data
        mock_alerts = [
            {"level": "warning", "message": "Price optimization suggestion available", "time": "2 min ago"},
            {"level": "info", "message": "Market data updated successfully", "time": "15 min ago"},
            {"level": "success", "message": "Auto-apply rule executed", "time": "1 hour ago"},
        ]
        
        for alert in mock_alerts:
            level = alert["level"]
            if level == "warning":
                badge_class = "warning"
                icon = "⚠️"
            elif level == "error":
                badge_class = "error"
                icon = "🚨"
            elif level == "success":
                badge_class = "success"
                icon = "✅"
            else:
                badge_class = "info"
                icon = "ℹ️"
                
            st.markdown(f"""
            <div class="card" style="margin-bottom: 0.5rem; padding: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;">
                    <span>{icon}</span>
                    <span class="badge {badge_class}" style="font-size: 0.625rem;">{level}</span>
                    <span>{alert['message']}</span>
                    <span style="margin-left: auto; color: #64748B; font-size: 0.75rem;">{alert['time']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

