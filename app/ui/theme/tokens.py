from __future__ import annotations

# Modern Light Theme Design System for FluxPricer AI

LIGHT = {
    # Primary colors
    "bg": "#FFFFFF",           # Pure white background
    "bg-alt": "#F8FAFC",       # Alternative light background
    "card": "#FFFFFF",         # Card background
    "surface": "#F1F5F9",      # Surface elements
    
    # Text colors
    "text": "#1E293B",         # Primary text - dark slate
    "text-secondary": "#475569", # Secondary text
    "text-muted": "#64748B",   # Muted text
    "text-disabled": "#94A3B8", # Disabled text
    
    # Brand colors
    "primary": "#3B82F6",      # Blue primary
    "primary-light": "#DBEAFE", # Light blue
    "primary-dark": "#1D4ED8",  # Dark blue
    
    # Semantic colors
    "success": "#10B981",      # Green
    "success-light": "#D1FAE5",
    "warning": "#F59E0B",      # Amber
    "warning-light": "#FEF3C7",
    "error": "#EF4444",        # Red
    "error-light": "#FEE2E2",
    "info": "#3B82F6",         # Blue
    "info-light": "#DBEAFE",
    
    # Neutral colors
    "border": "#E2E8F0",       # Light border
    "border-strong": "#CBD5E1", # Stronger border
    "hover": "#F1F5F9",        # Hover state
    "active": "#E2E8F0",       # Active state
    
    # Chart colors (light theme optimized)
    "chart-bg": "#FFFFFF",
    "chart-grid": "#F1F5F9",
    "chart-text": "#374151",
    "chart-colors": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4", "#F97316", "#84CC16"]
}

# Keep dark theme for future use but focus on light
DARK = {
    "bg": "#0B1220",
    "bg-alt": "#111827",
    "card": "#0F172A",
    "surface": "#1F2937",
    "text": "#E5E7EB",
    "text-secondary": "#D1D5DB",
    "text-muted": "#93A3B8",
    "text-disabled": "#6B7280",
    "primary": "#60A5FA",
    "primary-light": "#1E3A8A",
    "primary-dark": "#3B82F6",
    "success": "#34D399",
    "success-light": "#064E3B",
    "warning": "#FBBF24",
    "warning-light": "#78350F",
    "error": "#F87171",
    "error-light": "#7F1D1D",
    "info": "#60A5FA",
    "info-light": "#1E3A8A",
    "border": "#233044",
    "border-strong": "#2F3E55",
    "hover": "#111827",
    "active": "#233044",
    "chart-bg": "#1E293B",
    "chart-grid": "#374151",
    "chart-text": "#E5E7EB",
    "chart-colors": ["#60A5FA", "#34D399", "#FBBF24", "#F87171", "#A78BFA", "#22D3EE", "#FB7185", "#A3E635"]
}


def theme_css(dark: bool = False) -> str:
    t = DARK if dark else LIGHT
    return f"""
    <style>
    /* ===== MODERN LIGHT THEME - FLUXPRICER AI ===== */
    
    /* Root App Styling */
    .stApp {{ 
        background: linear-gradient(135deg, {t['bg']} 0%, {t['bg-alt']} 100%) !important;
        color: {t['text']} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }}
    /* Chat bubble CSS variables for theming */
    :root {{
        --bubble-user-bg-light: #F1F5F9;
        --bubble-user-border-light: #CBD5E1;
        --bubble-assistant-bg-light: #FFFFFF;
        --bubble-assistant-border-light: #E2E8F0;
        --bubble-user-bg-dark: #1F2937;
        --bubble-user-border-dark: #2F3E55;
        --bubble-assistant-bg-dark: #0F172A;
        --bubble-assistant-border-dark: #2F3E55;
    }}
    
    /* Remove Streamlit header/toolbar */
    .stAppHeader {{
        display: none !important;
    }}
    
    .stToolbar {{
        display: none !important;
    }}
    
    .stDecoration {{
        display: none !important;
    }}
    
    /* Fix any dark backgrounds */
    .stApp > header {{
        background: transparent !important;
        display: none !important;
    }}
    
    .stApp > header[data-testid="stHeader"] {{
        display: none !important;
    }}
    
    /* Remove any black bars or headers */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    
    .stApp .main-header {{
        display: none !important;
    }}
    
    /* Override any dark theme remnants */
    .stApp * {{
        background-color: initial !important;
    }}
    
    .stApp .element-container {{
        background: transparent !important;
    }}
    
    /* Main Content Area */
    .main .block-container {{
        background-color: transparent !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1200px !important;
    }}
    
    /* ===== SIDEBAR ===== */
    .stSidebar {{
        background: {t['card']} !important;
        border-right: 1px solid {t['border']} !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }}
    
    .stSidebar .sidebar-content {{
        background: transparent !important;
    }}
    
    .stSidebar * {{
        color: {t['text']} !important;
    }}
    
    .stSidebar h1, .stSidebar h2, .stSidebar h3 {{
        color: {t['text']} !important;
        font-weight: 600 !important;
    }}
    
    /* ===== TYPOGRAPHY ===== */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
        color: {t['text']} !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
    }}
    
    .stApp p, .stApp span, .stApp div {{
        color: {t['text']} !important;
    }}
    
    .stMarkdown {{
        color: {t['text']} !important;
    }}
    
    .stMarkdown * {{
        color: {t['text']} !important;
    }}
    
    /* ===== METRICS & CARDS ===== */
    .stMetric {{
        background: {t['card']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
    }}
    
    .stMetric:hover {{
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-1px) !important;
    }}
    
    .stMetric * {{
        color: {t['text']} !important;
    }}
    
    .stMetric [data-testid="metric-value"] {{
        color: {t['text']} !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }}
    
    .stMetric [data-testid="metric-delta"] {{
        color: {t['text-secondary']} !important;
    }}
    
    /* ===== BUTTONS ===== */
    .stButton > button {{
        background: {t['primary']} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }}
    
    .stButton > button:hover {{
        background: {t['primary-dark']} !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-1px) !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(0) !important;
    }}
    
    /* Secondary Button Style */
    .stButton.secondary > button {{
        background: {t['card']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['border']} !important;
    }}
    
    .stButton.secondary > button:hover {{
        background: {t['hover']} !important;
        border-color: {t['border-strong']} !important;
    }}
    
    /* ===== INPUTS ===== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {{
        background: {t['card']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 8px !important;
        transition: border-color 0.2s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stNumberInput > div > div > input:focus {{
        border-color: {t['primary']} !important;
        box-shadow: 0 0 0 3px {t['primary-light']} !important;
    }}

    /* ===== CHAT INPUT (st.chat_input) ===== */
    [data-testid="stChatInput"] {{
        background: {t['card']} !important;
        border-top: 1px solid {t['border']} !important;
        padding: 0.5rem 0 !important;
    }}

    [data-testid="stChatInput"] * {{
        color: {t['text']} !important;
    }}

    /* Text entry element inside chat input (covers textarea or contenteditable div) */
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] div[contenteditable="true"] {{
        background: {t['card']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 10px !important;
        padding: 0.6rem 0.75rem !important;
        outline: none !important;
    }}

    [data-testid="stChatInput"] textarea::placeholder {{
        color: {t['text-muted']} !important;
        opacity: 1 !important;
    }}
    
    /* ===== RADIO & CHECKBOXES ===== */
    .stRadio > div {{
        background: {t['card']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
    }}
    
    .stRadio * {{
        color: {t['text']} !important;
    }}
    
    .stCheckbox * {{
        color: {t['text']} !important;
    }}
    
    /* ===== TABLES & DATAFRAMES ===== */
    .stDataFrame {{
        background: {t['card']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }}
    
    .stDataFrame table {{
        background: {t['card']} !important;
        color: {t['text']} !important;
    }}
    
    .stDataFrame thead th {{
        background: {t['surface']} !important;
        color: {t['text']} !important;
        font-weight: 600 !important;
        border-bottom: 1px solid {t['border']} !important;
    }}
    
    .stDataFrame tbody td {{
        color: {t['text']} !important;
        border-bottom: 1px solid {t['border']} !important;
    }}
    
    .stDataFrame tbody tr:hover {{
        background: {t['hover']} !important;
    }}
    
    /* ===== EXPANDERS ===== */
    .streamlit-expanderHeader {{
        background: {t['card']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }}
    
    .streamlit-expanderContent {{
        background: {t['card']} !important;
        border: 1px solid {t['border']} !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }}
    
    /* ===== PLOTLY CHARTS ===== */
    .js-plotly-plot {{
        background: {t['chart-bg']} !important;
        border-radius: 8px !important;
        border: 1px solid {t['border']} !important;
    }}
    
    .js-plotly-plot .plotly {{
        background: {t['chart-bg']} !important;
    }}
    
    /* ===== CUSTOM COMPONENTS ===== */
    .card {{
        background: {t['card']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
    }}
    
    .card:hover {{
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-1px) !important;
    }}
    
    .card * {{
        color: {t['text']} !important;
    }}
    
    /* ===== STATUS BADGES ===== */
    .badge {{
        display: inline-block !important;
        padding: 0.25rem 0.75rem !important;
        border-radius: 9999px !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}
    
    .badge.success {{
        background: {t['success-light']} !important;
        color: {t['success']} !important;
    }}
    
    .badge.warning {{
        background: {t['warning-light']} !important;
        color: {t['warning']} !important;
    }}
    
    .badge.error {{
        background: {t['error-light']} !important;
        color: {t['error']} !important;
    }}
    
    .badge.info {{
        background: {t['info-light']} !important;
        color: {t['info']} !important;
    }}
    
    /* ===== UTILITY CLASSES ===== */
    .text-muted {{
        color: {t['text-muted']} !important;
    }}
    
    .text-secondary {{
        color: {t['text-secondary']} !important;
    }}
    
    .bg-surface {{
        background: {t['surface']} !important;
    }}
    
    /* ===== SCROLLBARS ===== */
    ::-webkit-scrollbar {{
        width: 8px !important;
        height: 8px !important;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {t['bg-alt']} !important;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {t['border-strong']} !important;
        border-radius: 4px !important;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {t['text-muted']} !important;
    }}
    
    /* ===== RESPONSIVE DESIGN ===== */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        
        .stMetric {{
            margin-bottom: 0.5rem !important;
        }}
    }}
    </style>
    """