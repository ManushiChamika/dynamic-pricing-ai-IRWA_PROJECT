from __future__ import annotations
import streamlit as st
import os
from datetime import datetime, timedelta, timezone
from app.ui.theme.inject import apply_theme
from core.auth_db import init_db
from core.auth_service import authenticate, create_persistent_session
from app.session_utils import COOKIE_NAME, cookie_mgr


def view() -> None:
    """Simplified, robust login page."""
    apply_theme(False)

    # Remove sidebar for auth pages
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .main > div { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

    # Initialize database
    init_db()

    # If already logged in, redirect to dashboard
    if st.session_state.get("session"):
        st.query_params["page"] = "dashboard"
        st.rerun()

    # Header Section
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🔐</div>
        <h1 style="color: #3B82F6; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">
            Welcome Back
        </h1>
        <p style="color: #64748B; font-size: 1.2rem; margin-bottom: 2rem;">
            Sign in to access your FluxPricer AI dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Login Form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); border: 1px solid #E2E8F0;">
        """, unsafe_allow_html=True)
        
        # Show success message if coming from registration
        if st.session_state.get("login_from_registration"):
            st.success("🎉 Account created successfully! Please sign in below.")
            st.session_state.pop("login_from_registration", None)

        with st.form("login_form", clear_on_submit=False):
            st.markdown("### 🔑 Login to Your Account")
            
            email = st.text_input(
                "📧 Email Address", 
                placeholder="you@example.com",
                help="Enter your registered email address"
            )
            password = st.text_input(
                "🔒 Password", 
                type="password",
                help="Enter your account password"
            )
            
            submitted = st.form_submit_button(
                "🚀 **Sign In**", 
                type="primary", 
                use_container_width=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Handle form submission
        if submitted:
            email_norm = (email or "").strip().lower()
            pw = (password or "").strip()

            if not email_norm or not pw:
                st.error("⚠️ Email and password are required.")
            else:
                try:
                    # Authenticate user
                    session = authenticate(email=email_norm, password=pw)
                    st.session_state["session"] = session

                    # Create server-side token
                    token, _ = create_persistent_session(session["user_id"])

                    # Set the cookie
                    cm = cookie_mgr()
                    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
                    cm.set(
                        COOKIE_NAME,
                        token,
                        expires_at=expires_at,
                        max_age=7*24*60*60,
                        path="/",
                        same_site="Lax",
                    )

                    # Success - redirect to dashboard
                    st.success("✅ Login successful! Redirecting to dashboard...")
                    st.balloons()
                    
                    # Small delay to let user see success message
                    import time
                    time.sleep(1)
                    
                    st.query_params["page"] = "dashboard" 
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ {str(e)}")

    # Navigation Section
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔗 Quick Actions")
        
        nav_col1, nav_col2 = st.columns(2)
        
        with nav_col1:
            if st.button("📝 **Create Account**", use_container_width=True):
                st.query_params["page"] = "register"
                st.rerun()
                
        with nav_col2:
            if st.button("🏠 **Back to Home**", use_container_width=True):
                st.query_params["page"] = "landing"
                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; color: #64748B;">
        <p>&copy; 2024 FluxPricer AI • Secure Authentication</p>
    </div>
    """, unsafe_allow_html=True)