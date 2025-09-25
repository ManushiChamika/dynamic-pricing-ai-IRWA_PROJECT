from __future__ import annotations

# Theme tokens and a small CSS generator for Streamlit

LIGHT = {
    "bg": "#F7F9FC",
    "card": "#FFFFFF",
    "text": "#0F172A",
    "muted": "#475569",
    "accent": "#2563EB",
    "accent-weak": "#93C5FD",
    "border": "#E2E8F0",
    "info": "#2563EB",
    "warn": "#D97706",
    "crit": "#DC2626",
}

DARK = {
    "bg": "#0B1220",
    "card": "#111827",
    "text": "#E5E7EB",
    "muted": "#94A3B8",
    "accent": "#60A5FA",
    "accent-weak": "#1E3A8A",
    "border": "#1F2937",
    "info": "#60A5FA",
    "warn": "#F59E0B",
    "crit": "#F87171",
}


def theme_css(dark: bool = False) -> str:
    t = DARK if dark else LIGHT
    return f"""
    <style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    .stMetric, .stButton>button, .stTextInput>div>div>input, .stSelectbox>div>div>div {{
        border-radius: 10px; border: 1px solid {t['border']};
    }}
    .stMetric {{ background-color: {t['card']}; }}
    .card {{ background: {t['card']}; border: 1px solid {t['border']}; border-radius: 12px; padding: 16px; }}
    .muted {{ color: {t['muted']}; }}
    .badge {{ display:inline-block; padding: 2px 8px; border-radius: 999px; font-size:12px; }}
    .badge.info {{ background: {t['accent-weak']}; color: {t['text']}; }}
    .badge.warn {{ background: #FEF3C7; color: #92400E; }}
    .badge.crit {{ background: #FEE2E2; color: #991B1B; }}
    </style>
    """