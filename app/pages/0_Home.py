from app.session_utils import COOKIE_NAME, cookie_mgr, ensure_session_from_cookie
from core.auth_service import revoke_session_token
import streamlit as st, pathlib

# ————————————————————————————————————————————————————————————————
# Page config
# ————————————————————————————————————————————————————————————————
st.set_page_config(
    page_title="FluxPricer AI — Home",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "FluxPricer AI — demo for coursework. Not for production use."
    },
)

# ————————————————————————————————————————————————————————————————
# Global Styles (Professional, Modern, Accessible)
# ————————————————————————————————————————————————————————————————
st.markdown(
    """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

  :root {
    --primary: #4f46e5;           /* Indigo 600 */
    --primary-dark: #4338ca;      /* Indigo 700 */
    --primary-light: #818cf8;     /* Indigo 400 */
    --secondary: #7c3aed;         /* Violet 600 */
    --accent1: #a78bfa;           /* Violet 400 */
    --accent2: #e0e7ff;           /* Indigo 100 */
    --dark: #111827;              /* Gray 900 */
    --dark-light: #1f2937;        /* Gray 800 */
    --muted: #6b7280;             /* Gray 500 */
    --muted-light: #9ca3af;       /* Gray 400 */
    --light: #f9fafb;             /* Slate 50 */
    --light-dark: #f3f4f6;        /* Gray 100 */
    --success: #10b981;           /* Emerald 500 */
    --warning: #f59e0b;           /* Amber 500 */
    --danger: #ef4444;            /* Red 500 */
    --info: #0ea5e9;              /* Sky 500 */
    --card: #ffffff;
    --card-dark: #f8fafc;
    --border: #e5e7eb;
    --border-light: #f1f5f9;
    --shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
    --glow: 0 0 20px 5px rgba(79, 70, 229, 0.15);
  }

  /* Base */
  html, body, [class^="block-container"] {
    font-family: 'Inter', 'Plus Jakarta Sans', system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial;
    background: linear-gradient(180deg, #6366f1 0%, #ec4899 100%);
    color: var(--dark);
    scroll-behavior: smooth;
  }

  /* Container width */
  section.main > div {
    max-width: 1200px;
    margin: auto;
    padding-top: 1.5rem;
  }

  /* Hide default Streamlit header and decoration */
  header[data-testid="stHeader"] { 
    background: transparent; 
    height: 0;
    padding: 0;
  }
  .decoration {
    display: none;
  }

  /* Smooth hover lift */
  .lift { 
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
  }
  .lift:hover { 
    transform: translateY(-5px); 
    box-shadow: var(--shadow-xl);
  }

  /* Hero */
  .hero {
    position: relative;
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    border-radius: 24px;
    padding: 4rem 2rem;
    color: white;
    text-align: center;
    max-width: 1100px;
    margin: 2rem auto 3rem;
    box-shadow: var(--shadow-xl), var(--glow);
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    transform: rotate(30deg);
  }
  .hero h1{ 
    font-size: 3rem; 
    font-weight: 800; 
    margin-bottom: 1rem;
    letter-spacing: -0.025em;
    position: relative;
    z-index: 2;
  }
  .hero p{ 
    font-size: 1.25rem; 
    opacity: .9; 
    margin: 0 auto; 
    max-width: 800px;
    font-weight: 400;
    position: relative;
    z-index: 2;
  }

  /* Cards */
  .card {
    background: var(--card);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 1.75rem;
    box-shadow: var(--shadow);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
    position: relative;
    overflow: hidden;
  }
  .card::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary), var(--secondary));
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  .card:hover::after {
    opacity: 1;
  }
  .card:hover { 
    transform: translateY(-5px); 
    box-shadow: var(--shadow-xl);
    border-color: var(--accent2);
  }
  
  .agent-card { 
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .agent-card .icon-container{ 
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    border-radius: 16px;
    width: 70px;
    height: 70px;
    display:flex;
    align-items:center;
    justify-content:center;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-lg);
  }
  .agent-card .icon{ 
    font-size: 2rem; 
    color: white;
  }
  .agent-card h4{ 
    margin:0.75rem 0 0.5rem; 
    font-weight: 700; 
    font-size: 1.25rem;
    color: var(--dark);
  }
  .agent-card p{ 
    margin: 0; 
    color: var(--muted); 
    font-size: 0.95rem; 
    line-height: 1.5;
  }

  /* Metrics */
  .metric { 
    text-align: center;
    padding: 1.5rem;
  }
  .metric h3{ 
    margin:.5rem 0 0; 
    font-size: 2rem; 
    font-weight:800; 
    letter-spacing: -0.025em;
  }
  .kicker{ 
    text-transform: uppercase; 
    letter-spacing: .12em; 
    font-size: .75rem; 
    color: var(--muted); 
    margin-bottom:.5rem;
    font-weight: 600;
  }

  /* Buttons */
  .stButton > button {
    width: 100%; 
    font-weight: 600; 
    border-radius: 12px; 
    border: 0; 
    padding: .875rem 1.5rem;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: #fff; 
    box-shadow: var(--shadow);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-size: 1rem;
    position: relative;
    overflow: hidden;
  }
  .stButton > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: all 0.6s ease;
  }
  .stButton > button:hover::before {
    left: 100%;
  }
  .stButton > button:hover { 
    transform: translateY(-2px); 
    box-shadow: var(--shadow-xl);
  }
  .stButton > button:active { 
    transform: translateY(0); 
  }

  .btn-secondary > button { 
    background: #fff; 
    color: var(--primary); 
    border: 1px solid var(--border); 
    box-shadow: var(--shadow);
  }
  .btn-secondary > button:hover { 
    background: #f5f3ff; 
    border-color: var(--primary-light);
  }

  .btn-danger > button { 
    background: linear-gradient(135deg, var(--danger), #fb7185); 
    box-shadow: var(--shadow);
  }
  .btn-danger > button:hover {
    box-shadow: 0 10px 15px -3px rgba(239, 68, 68, 0.3), 0 4px 6px -2px rgba(239, 68, 68, 0.15);
  }

  /* Modal */
  .overlay { 
    position: fixed; 
    inset: 0; 
    background: rgba(17,24,39,.65); 
    z-index: 999; 
    backdrop-filter: blur(4px);
    animation: fadeIn 0.2s ease;
  }
  .modal { 
    position: fixed; 
    inset: 50% auto auto 50%; 
    transform: translate(-50%, -50%); 
    z-index: 1000; 
    width: 420px; 
    max-width: 92vw; 
    animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .modal .content{ 
    background: #fff; 
    border-radius: 20px; 
    padding: 2rem; 
    box-shadow: var(--shadow-xl);
    border: 1px solid var(--border-light);
  }

  /* Footer */
  .footer { 
    text-align: center; 
    color: var(--muted); 
    border-top: 1px solid var(--border);
    padding: 1.5rem 0 1rem; 
    font-size: .875rem; 
    margin-top: 4rem;
    background: var(--light);
    border-radius: 0 0 12px 12px;
  }

  /* Animations */
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  @keyframes slideIn {
    from { 
      opacity: 0;
      transform: translate(-50%, -48%);
    }
    to { 
      opacity: 1;
      transform: translate(-50%, -50%);
    }
  }

  /* Utility */
  .center { 
    display:flex; 
    align-items:center; 
    justify-content:center; 
  }
  .mb-0{ margin-bottom:0; } 
  .mb-2{ margin-bottom:.5rem; } 
  .mb-3{ margin-bottom:1rem; } 
  .mb-4{ margin-bottom:1.5rem; }
  .mt-2 { margin-top: 0.5rem; }
  .mt-4 { margin-top: 1.5rem; }
  
  /* Section headers */
  .section-header {
    font-size: 2rem;
    font-weight: 700;
    color: var(--dark);
    margin: 2.5rem 0 1.5rem;
    position: relative;
    display: inline-block;
  }
  .section-header::after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 0;
    width: 50px;
    height: 4px;
    background: linear-gradient(90deg, var(--primary), var(--secondary));
    border-radius: 2px;
  }
  
  /* Divider */
  .stDivider {
    margin: 3rem 0;
  }
  
  /* Gradient text */
  .gradient-text {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
</style>
""",
    unsafe_allow_html=True,
)

# ————————————————————————————————————————————————————————————————
# Session bootstrap
# ————————————————————————————————————————————————————————————————
ensure_session_from_cookie("home")

# ————————————————————————————————————————————————————————————————
# HERO
# ————————————————————————————————————————————————————————————————
st.markdown('<div class="hero">', unsafe_allow_html=True)

logo_path = pathlib.Path("assets/logo.svg")
if logo_path.exists():
    st.markdown('<div class="center mb-3">' + logo_path.read_text() + '</div>', unsafe_allow_html=True)
else:
    st.markdown('<h1 class="center mb-0 gradient-text">FluxPricer AI</h1>', unsafe_allow_html=True)

# Main title
st.markdown('<h1 style="margin-bottom: 1rem;">Real-time Dynamic Pricing for Fashion & Accessories</h1>', unsafe_allow_html=True)

# Subtitle
st.markdown(
    '<p style="margin-top:0.5rem; opacity:.9; font-size: 1.25rem;">Multi-agent system delivering intelligent pricing decisions with real-time market adaptation</p>',
    unsafe_allow_html=True
)

# ✅ Show robot image (center + larger)
robot_path = pathlib.Path("assets/home_pricing2.png")
if robot_path.exists():
    st.markdown('<div class="center mt-4">', unsafe_allow_html=True)
    st.image(str(robot_path), width=1000, use_column_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# ————————————————————————————————————————————————————————————————
# Agents Grid
# ————————————————————————————————————————————————————————————————
st.markdown('<h2 class="section-header">🤖 Our Intelligent Agent System</h2>', unsafe_allow_html=True)
st.caption("Four specialized AI agents working in harmony to optimize your pricing strategy")

c1, c2, c3, c4 = st.columns(4, gap="large")
with c1:
    st.markdown("""
    <div class="card lift agent-card">
        <div class="icon-container">
            <div class="icon">📊</div>
        </div>
        <h4>Market Data Collector</h4>
        <p>Gathers and preprocesses competitor pricing, sales history, and external market signals in real time.</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="card lift agent-card">
        <div class="icon-container">
            <div class="icon">🤖</div>
        </div>
        <h4>Price Optimizer</h4>
        <p>ML models and constrained optimization converge on ideal prices across products and regions.</p>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown("""
    <div class="card lift agent-card">
        <div class="icon-container">
            <div class="icon">🔔</div>
        </div>
        <h4>Alert & Notification Agent</h4>
        <p>Monitors market shocks and notifies you of opportunities or risks instantly.</p>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown("""
    <div class="card lift agent-card">
        <div class="icon-container">
            <div class="icon">👤</div>
        </div>
        <h4>User Interaction</h4>
        <p>Intuitive dashboards, clear explanations of model decisions, and safe manual overrides.</p>
    </div>
    """, unsafe_allow_html=True)

# ————————————————————————————————————————————————————————————————
# Primary Actions
# ————————————————————————————————————————————————————————————————
st.markdown('<h2 class="section-header">Get Started</h2>', unsafe_allow_html=True)
a1, a2, a3 = st.columns(3, gap="large")

if st.session_state.get("session"):
    with a1:
        st.markdown("""
        <div class="card lift">
            <div class="kicker">Navigation</div>
            <h4 style="margin: 0.5rem 0 1rem;">Alerts & Notifications</h4>
        """, unsafe_allow_html=True)
        if st.button("View Alerts →", key="btn_alerts", use_container_width=True):
            st.switch_page("pages/5_Alerts_and_Notifications.py")
        st.markdown('</div>', unsafe_allow_html=True)

    with a2:
        st.markdown("""
        <div class="card lift">
            <div class="kicker">Account</div>
            <h4 style="margin: 0.5rem 0 1rem;">Profile Settings</h4>
        """, unsafe_allow_html=True)
        if st.button("Manage Profile →", key="btn_profile", use_container_width=True):
            st.switch_page("pages/4_Profile.py")
        st.markdown('</div>', unsafe_allow_html=True)

    with a3:
        st.markdown("""
        <div class="card lift">
            <div class="kicker">Session</div>
            <h4 style="margin: 0.5rem 0 1rem;">Logout</h4>
        """, unsafe_allow_html=True)
        st.markdown('<div class="stButton btn-danger">', unsafe_allow_html=True)
        logout_clicked = st.button("Logout →", key="logout_btn", use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
        if logout_clicked:
            st.session_state["confirm_logout"] = True

    # Logout confirmation modal
    if st.session_state.get("confirm_logout"):
        st.markdown('<div class="overlay"></div>', unsafe_allow_html=True)
        st.markdown('<div class="modal"><div class="content">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-top: 0;">Confirm Logout</h3>', unsafe_allow_html=True)
        st.warning("Are you sure you want to log out?")
        mc1, mc2 = st.columns(2)
        with mc1:
            if st.button("✅ Yes, log out", key="logout_yes", use_container_width=True):
                tok = st.session_state.get("session", {}).get("token")
                if tok:
                    try: revoke_session_token(tok)
                    except Exception: pass
                st.session_state.pop("session", None)
                st.session_state["_skip_cookie_restore_once"] = True
                st.session_state.pop("confirm_logout", None)
                st.switch_page("pages/_logout.py")
        with mc2:
            st.markdown('<div class="stButton btn-secondary">', unsafe_allow_html=True)
            if st.button("❌ Cancel", key="logout_cancel", use_container_width=True):
                st.session_state.pop("confirm_logout", None)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

else:
    with a1:
        st.markdown("""
        <div class="card lift">
            <div class="kicker">Welcome back</div>
            <h4 style="margin: 0.5rem 0 1rem;">Existing User</h4>
        """, unsafe_allow_html=True)
        if st.button("🔑 Login →", key="btn_login", use_container_width=True):
            st.switch_page("pages/1_Login.py")
        st.markdown('</div>', unsafe_allow_html=True)
    with a2:
        st.markdown("""
        <div class="card lift">
            <div class="kicker">New here?</div>
            <h4 style="margin: 0.5rem 0 1rem;">Create Account</h4>
        """, unsafe_allow_html=True)
        st.markdown('<div class="stButton btn-secondary">', unsafe_allow_html=True)
        if st.button("✨ Sign Up →", key="btn_register", use_container_width=True):
            st.switch_page("pages/2_Register.py")
        st.markdown('</div></div>', unsafe_allow_html=True)
    a3.write("")


# ————————————————————————————————————————————————————————————————
# Status Summary
# ————————————————————————————————————————————————————————————————
st.divider()

s1, s2, s3 = st.columns(3, gap="large")

auth_state = "Logged in" if st.session_state.get("session") else "Guest"
status_color = "var(--success)" if st.session_state.get("session") else "var(--warning)"

with s1:
    st.markdown(f'<div class="card metric lift"><div class="kicker">Auth Status</div><h3 style="color:{status_color}">{auth_state}</h3></div>', unsafe_allow_html=True)
with s2:
    st.markdown('<div class="card metric lift"><div class="kicker">Active Agents</div><h3 style="color: var(--info)">4</h3></div>', unsafe_allow_html=True)
with s3:
    st.markdown('<div class="card metric lift"><div class="kicker">Monitoring</div><h3 style="color: var(--primary)">24/7</h3></div>', unsafe_allow_html=True)

# ————————————————————————————————————————————————————————————————
# Incidents (live — extras)
# ————————————————————————————————————————————————————————————————
# ————————————————————————————————————————————————————————————————
# Footer
# ————————————————————————————————————————————————————————————————
st.markdown('<div class="footer">FluxPricer AI ©</div>', unsafe_allow_html=True)