import streamlit as st
from .tokens import theme_css


def apply_theme(dark: bool = False) -> None:
    st.markdown(theme_css(dark), unsafe_allow_html=True)
