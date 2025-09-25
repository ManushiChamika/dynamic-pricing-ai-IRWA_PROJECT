from __future__ import annotations
import streamlit as st
from datetime import datetime
from app.ui.theme.inject import apply_theme


def view() -> None:
    """
    Landing page - separate from dashboard navigation.
    This should be the first page users see when they visit the app.
    """
    apply_theme(False)

    # Remove sidebar for landing page
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .main > div { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

    # Hero Section
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🚀</div>
        <h1 style="color: #3B82F6; font-size: 3.5rem; margin-bottom: 1rem; font-weight: 700;">
            FluxPricer AI
        </h1>
        <p style="color: #64748B; font-size: 1.5rem; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">
            The most advanced AI-powered dynamic pricing platform for modern businesses
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Call-to-Action Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 **Enter Dashboard**", type="primary", use_container_width=True):
            # Set query params to navigate to dashboard
            st.query_params["page"] = "dashboard"
            st.rerun()

    st.markdown("---")

    # Feature Highlights
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h2 style="color: #1F2937; margin-bottom: 2rem;">Why Choose FluxPricer AI?</h2>
    </div>
    """, unsafe_allow_html=True)

    # Features Grid
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
            <h3 style="color: #3B82F6; margin-bottom: 1rem;">AI-Powered Intelligence</h3>
            <p style="color: #64748B;">
                Advanced machine learning algorithms analyze market conditions, 
                competitor pricing, and demand patterns in real-time.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
            <h3 style="color: #3B82F6; margin-bottom: 1rem;">Lightning Fast</h3>
            <p style="color: #64748B;">
                Instant price optimization with automated rule execution. 
                React to market changes faster than your competition.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card" style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💰</div>
            <h3 style="color: #3B82F6; margin-bottom: 1rem;">Maximize Revenue</h3>
            <p style="color: #64748B;">
                Increase profits by up to 25% with intelligent pricing strategies 
                that adapt to market dynamics automatically.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Key Features Section
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0;">
        <h2 style="color: #1F2937; margin-bottom: 2rem;">Powerful Features</h2>
    </div>
    """, unsafe_allow_html=True)

    # Features List
    feature_col1, feature_col2 = st.columns(2)

    with feature_col1:
        st.markdown("""
        <div class="card">
            <h4 style="color: #3B82F6; margin-bottom: 1rem;">🧠 Multi-Agent AI System</h4>
            <ul style="color: #64748B; line-height: 1.8;">
                <li>Data Collection Agents for market intelligence</li>
                <li>Price Optimization AI with ML algorithms</li>
                <li>Alert Service for real-time notifications</li>
                <li>Policy Guard for business rule compliance</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card" style="margin-top: 1rem;">
            <h4 style="color: #3B82F6; margin-bottom: 1rem;">📊 Advanced Analytics</h4>
            <ul style="color: #64748B; line-height: 1.8;">
                <li>Real-time performance dashboards</li>
                <li>Revenue optimization reports</li>
                <li>Market trend analysis</li>
                <li>Competitor price monitoring</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with feature_col2:
        st.markdown("""
        <div class="card">
            <h4 style="color: #3B82F6; margin-bottom: 1rem;">💬 Natural Language Interface</h4>
            <ul style="color: #64748B; line-height: 1.8;">
                <li>Chat with AI for pricing insights</li>
                <li>Ask questions in plain English</li>
                <li>Get instant recommendations</li>
                <li>Voice-activated commands</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card" style="margin-top: 1rem;">
            <h4 style="color: #3B82F6; margin-bottom: 1rem;">⚡ Automation & Control</h4>
            <ul style="color: #64748B; line-height: 1.8;">
                <li>Automated pricing rules</li>
                <li>Smart alert system</li>
                <li>Batch price updates</li>
                <li>Schedule-based optimization</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Get Started Section
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h2 style="color: #1F2937; margin-bottom: 1rem;">Ready to Transform Your Pricing?</h2>
        <p style="color: #64748B; font-size: 1.2rem; margin-bottom: 2rem;">
            Join thousands of businesses already using FluxPricer AI to maximize their revenue
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Final CTA
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        cta_col1, cta_col2 = st.columns(2)
        
        with cta_col1:
            if st.button("🚀 **Launch Dashboard**", type="primary", use_container_width=True):
                st.query_params["page"] = "dashboard"
                st.rerun()
                
        with cta_col2:
            if st.button("💬 **Try AI Chat**", use_container_width=True):
                st.query_params["page"] = "dashboard"
                st.query_params["section"] = "chat"
                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; color: #64748B;">
        <p>&copy; 2024 FluxPricer AI • Powered by Advanced Machine Learning</p>
    </div>
    """, unsafe_allow_html=True)