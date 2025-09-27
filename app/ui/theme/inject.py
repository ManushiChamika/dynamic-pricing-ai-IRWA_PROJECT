import streamlit as st
from .tokens import theme_css


def apply_theme(dark: bool | None = None) -> None:
    """Apply theme; if dark is None, read from session state toggle."""
    if dark is None:
        dark = bool(st.session_state.get("is_dark_mode", False))
    st.session_state["is_dark_mode"] = bool(dark)
    # Set CSS variables (including typing bubble) so UI can theme correctly
    bubble_css = """
    <style>
    :root {
      --bubble-user-bg: %s;
      --bubble-user-border: %s;
      --bubble-assistant-bg: %s;
      --bubble-assistant-border: %s;
      --bubble-fg: %s;

            /* Typing bubble ("Thinking…") theme-aware variables */
            --typing-bg: %s;
            --typing-border: %s;
            --typing-fg: %s;
            --typing-dot-start: %s;
            --typing-dot-end: %s;
    }
    </style>
    """ % (
        ("var(--bubble-user-bg-dark)" if dark else "var(--bubble-user-bg-light)"),
        ("var(--bubble-user-border-dark)" if dark else "var(--bubble-user-border-light)"),
        ("var(--bubble-assistant-bg-dark)" if dark else "var(--bubble-assistant-bg-light)"),
        ("var(--bubble-assistant-border-dark)" if dark else "var(--bubble-assistant-border-light)"),
        ("#E5E7EB" if dark else "#111827"),
        # typing bubble colors
    ("linear-gradient(135deg, rgba(30, 41, 59, 0.92) 0%, rgba(11, 23, 46, 0.98) 100%)" if dark else "linear-gradient(135deg, #EFF6FF 0%, #EEF2FF 100%)"),
    ("rgba(71, 85, 105, 0.55)" if dark else "#BFDBFE"),
    ("#E9EEF7" if dark else "#1E3A8A"),
    ("#8BB4FF" if dark else "#3B82F6"),
    ("#4A7DFF" if dark else "#1D4ED8"),
    )
    st.markdown(theme_css(bool(dark)) + bubble_css, unsafe_allow_html=True)
    st.session_state["theme_applied"] = True
