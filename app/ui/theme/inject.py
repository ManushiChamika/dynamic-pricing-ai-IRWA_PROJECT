import streamlit as st
from .tokens import theme_css


def apply_theme(dark: bool = False) -> None:
    """Apply theme with high contrast colors for better visibility"""
    st.markdown(theme_css(dark), unsafe_allow_html=True)
    
    # Force theme application at session level
    if "theme_applied" not in st.session_state:
        st.session_state.theme_applied = True
