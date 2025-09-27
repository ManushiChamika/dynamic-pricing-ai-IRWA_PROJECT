from __future__ import annotations
import streamlit as st
from app.ui.theme.inject import apply_theme


def view() -> None:
    """Clean, simple landing page with working navigation."""
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
            AI-powered dynamic pricing platform for modern businesses
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Main Navigation Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Dashboard button
        if st.button("🚀 **Enter Dashboard**", type="primary", use_container_width=True):
            st.query_params["page"] = "dashboard"
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Auth buttons
        auth_col1, auth_col2 = st.columns(2)
        
        with auth_col1:
            if st.button("🔐 **Login**", use_container_width=True):
                st.query_params["page"] = "login"
                st.rerun()
                
        with auth_col2:
            if st.button("📝 **Register**", use_container_width=True):
                st.query_params["page"] = "register"
                st.rerun()

    st.markdown("---")

    # Features Section
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h2 style="color: #1F2937; margin-bottom: 2rem;">Why Choose FluxPricer AI?</h2>
    </div>
    """, unsafe_allow_html=True)

    # Feature Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
            <h3 style="color: #3B82F6; margin-bottom: 1rem;">AI-Powered</h3>
            <p style="color: #64748B;">
                Advanced machine learning algorithms analyze market conditions and optimize pricing in real-time.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
            <h3 style="color: #3B82F6; margin-bottom: 1rem;">Lightning Fast</h3>
            <p style="color: #64748B;">
                Instant price optimization with automated execution. React faster than your competition.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💰</div>
            <h3 style="color: #3B82F6; margin-bottom: 1rem;">Maximize Revenue</h3>
            <p style="color: #64748B;">
                Increase profits with intelligent pricing strategies that adapt automatically.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Call to Action
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h2 style="color: #1F2937; margin-bottom: 1rem;">Ready to Get Started?</h2>
        <p style="color: #64748B; font-size: 1.2rem; margin-bottom: 2rem;">
            Transform your pricing strategy with AI
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Final CTA Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        cta_col1, cta_col2 = st.columns(2)
        
        with cta_col1:
            if st.button("🚀 **Try Dashboard**", type="primary", use_container_width=True):
                st.query_params["page"] = "dashboard"
                st.rerun()
                
        with cta_col2:
            if st.button("📝 **Create Account**", use_container_width=True):
                st.query_params["page"] = "register"
                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; color: #64748B;">
        <p>&copy; 2024 FluxPricer AI</p>
    </div>
    """, unsafe_allow_html=True)