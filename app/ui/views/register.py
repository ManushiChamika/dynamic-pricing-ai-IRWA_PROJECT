from __future__ import annotations
import streamlit as st
import os
from app.ui.theme.inject import apply_theme
from core.auth_db import init_db
from core.auth_service import RegisterIn, register_user
from app.session_utils import ensure_session_from_cookie


def view() -> None:
    """
    Modern registration page - part of the new UI system.
    Integrates with existing authentication backend.
    """
    apply_theme(False)

    # Remove sidebar for auth pages
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .main > div { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

    # Initialize database and session management
    init_db()
    ensure_session_from_cookie()

    # Already logged in? Go to dashboard
    if st.session_state.get("session"):
        if os.getenv("DEBUG_LLM", "0") == "1":
            print("[DEBUG] User already logged in, redirecting to dashboard")
        st.query_params.clear()
        st.query_params["page"] = "dashboard"
        st.rerun()

    # Header Section
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📝</div>
        <h1 style="color: #3B82F6; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">
            Join FluxPricer AI
        </h1>
        <p style="color: #64748B; font-size: 1.2rem; margin-bottom: 2rem;">
            Create your account and start optimizing prices with AI
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Registration Form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); border: 1px solid #E2E8F0;">
        """, unsafe_allow_html=True)
        
        with st.form("register_form", clear_on_submit=False):
            st.markdown("### 🆕 Create Your Account")
            
            email = st.text_input(
                "📧 Email Address", 
                placeholder="you@example.com",
                help="Enter a valid email address for your account"
            )
            full_name = st.text_input(
                "👤 Full Name (Optional)", 
                placeholder="John Doe",
                help="Your full name for personalization"
            )
            password = st.text_input(
                "🔒 Password", 
                type="password",
                help="Must be at least 10 characters long"
            )
            
            # Password strength indicator
            if password:
                if len(password) < 10:
                    st.markdown("🔴 **Password too short** (minimum 10 characters)")
                elif len(password) < 15:
                    st.markdown("🟡 **Password strength: Fair**")
                else:
                    st.markdown("🟢 **Password strength: Strong**")
            
            submitted = st.form_submit_button(
                "🚀 **Create Account**", 
                type="primary", 
                use_container_width=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # Handle form submission
    if submitted:
        email_norm = (email or "").strip().lower()
        full_name_norm = (full_name or "").strip() or None
        pw = (password or "").strip()

        # Client-side validation
        if not email_norm:
            st.error("⚠️ Email address is required.")
        elif len(pw) < 10:
            st.error("⚠️ Password must be at least 10 characters long.")
        else:
            try:
                if os.getenv("DEBUG_LLM", "0") == "1":
                    print(f"[DEBUG] Attempting registration for email: {email_norm}")
                
                # Register user
                register_user(RegisterIn(
                    email=email_norm,
                    full_name=full_name_norm,
                    password=pw,
                ))
                
                st.success("✅ Account created successfully! Please log in.")
                
                # Auto-redirect to login page after success
                st.session_state["_registration_success"] = True
                if os.getenv("DEBUG_LLM", "0") == "1":
                    print("[DEBUG] Registration successful, redirecting to login")
                st.query_params.clear()
                st.query_params["page"] = "login"
                st.rerun()
                
            except Exception as e:
                if os.getenv("DEBUG_LLM", "0") == "1":
                    print(f"[DEBUG] Registration failed: {e}")
                st.error(f"❌ {str(e)}")

    # Navigation Section
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔗 Quick Actions")
        
        nav_col1, nav_col2 = st.columns(2)
        
        with nav_col1:
            if st.button("🔐 **Already Have Account?**", use_container_width=True):
                if os.getenv("DEBUG_LLM", "0") == "1":
                    print("[DEBUG] Navigating to login page")
                st.query_params.clear()
                st.query_params["page"] = "login"
                st.rerun()
                
        with nav_col2:
            if st.button("🏠 **Back to Home**", use_container_width=True):
                if os.getenv("DEBUG_LLM", "0") == "1":
                    print("[DEBUG] Navigating back to landing page")
                st.query_params.clear()
                st.query_params["page"] = "landing"
                st.rerun()

    # Benefits Section
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h3 style="color: #1F2937; margin-bottom: 2rem;">🌟 What You'll Get</h3>
    </div>
    """, unsafe_allow_html=True)

    benefit_col1, benefit_col2, benefit_col3 = st.columns(3)
    
    with benefit_col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
            <h4 style="color: #3B82F6; margin-bottom: 0.5rem;">AI-Powered Insights</h4>
            <p style="color: #64748B; font-size: 0.9rem;">Advanced pricing algorithms and market analysis</p>
        </div>
        """, unsafe_allow_html=True)

    with benefit_col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
            <h4 style="color: #3B82F6; margin-bottom: 0.5rem;">Real-Time Optimization</h4>
            <p style="color: #64748B; font-size: 0.9rem;">Instant price adjustments based on market conditions</p>
        </div>
        """, unsafe_allow_html=True)

    with benefit_col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
            <h4 style="color: #3B82F6; margin-bottom: 0.5rem;">Revenue Growth</h4>
            <p style="color: #64748B; font-size: 0.9rem;">Maximize profits with intelligent pricing strategies</p>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; color: #64748B;">
        <p>&copy; 2024 FluxPricer AI • Secure Registration</p>
    </div>
    """, unsafe_allow_html=True)