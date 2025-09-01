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
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Montserrat:wght@300;400;600;700&display=swap');

  :root {
    --primary: #4f46e5;      /* Indigo 600 */
    --secondary: #7c3aed;    /* Violet 600 */
    --accent1: #a78bfa;      /* Violet 400 */
    --accent2: #e0e7ff;      /* Indigo 100 */
    --dark: #111827;         /* Gray 900 */
    --muted: #6b7280;        /* Gray 500 */
    --light: #f9fafb;        /* Slate 50 */
    --success: #16a34a;      /* Green 600 */
    --warning: #f59e0b;      /* Amber 500 */
    --danger: #ef4444;       /* Red 500 */
    --info: #0ea5e9;         /* Sky 500 */
    --card: #fff;
    --border: #e5e7eb;
    --shadow: 0 8px 24px rgba(0,0,0,0.08);
  }

  /* Base */
  html, body, [class^="block-container"] {
    font-family: 'Inter', 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial;
    background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
    color: var(--dark);
  }

  /* Container width */
  section.main > div {
    max-width: 1200px;
    margin: auto;
    padding-top: 1.5rem;
  }

  /* Hide default Streamlit header */
  header[data-testid="stHeader"] { background: transparent; }

  /* Smooth hover lift */
  .lift { transition: transform .25s ease, box-shadow .25s ease; }
  .lift:hover { transform: translateY(-4px); box-shadow: var(--shadow); }

  /* Hero */
  .hero {
    position: relative;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    border-radius: 24px;
    padding: 3rem 2rem;
    color: white;
    text-align: center;
    max-width: 1100px;
    margin: auto;
    box-shadow: 0 12px 40px rgba(79,70,229,0.25);
  }
  .hero h1{ font-size: 2.5rem; font-weight: 800; margin-bottom: .5rem; }
  .hero p{ font-size: 1.125rem; opacity: .9; margin: 0 auto; max-width: 800px; }

  /* Cards */
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.05);
    transition: transform .25s ease, box-shadow .25s ease;
  }
  .card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
  .agent-card .icon{ font-size: 2rem; line-height: 1; color: white; background: linear-gradient(135deg, var(--primary), var(--secondary)); border-radius: 12px; width: 52px; height: 52px; display:flex; align-items:center; justify-content:center; margin-bottom: .75rem; }
  .agent-card h4{ margin:.5rem 0; font-weight: 700; }
  .agent-card p{ margin: 0; color: var(--muted); font-size: .925rem; }

  /* Metrics */
  .metric { text-align: center; }
  .metric h3{ margin:.25rem 0 0; font-size: 1.75rem; font-weight:700; }
  .kicker{ text-transform: uppercase; letter-spacing: .12em; font-size: .75rem; color: var(--muted); margin-bottom:.25rem; }

  /* Buttons */
  .stButton>button {
    width: 100%; font-weight: 600; border-radius: 10px; border: 0; padding: .75rem 1rem;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: #fff; box-shadow: 0 8px 24px rgba(79,70,229,0.28);
    transition: transform .2s ease, box-shadow .2s ease, opacity .2s ease;
  }
  .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 12px 28px rgba(79,70,229,0.38); }
  .stButton>button:active { transform: translateY(0); }

  .btn-secondary>button { background: #fff; color: var(--primary); border: 2px solid var(--accent1); box-shadow: none; }
  .btn-secondary>button:hover { background: #f5f3ff; }

  .btn-danger>button { background: linear-gradient(135deg, var(--danger), #fb7185); box-shadow: 0 8px 24px rgba(239,68,68,.25); }

  /* Modal */
  .overlay { position: fixed; inset: 0; background: rgba(17,24,39,.55); z-index: 999; }
  .modal { position: fixed; inset: 50% auto auto 50%; transform: translate(-50%, -50%); z-index: 1000; width: 420px; max-width: 92vw; }
  .modal .content{ background: #fff; border-radius: 16px; padding: 1.5rem; box-shadow: 0 20px 50px rgba(0,0,0,.2); }

  /* Footer */
  .footer { text-align: center; color: var(--muted); border-top: 1px solid #e5e7eb; padding: 1.25rem 0 .5rem; font-size: .875rem; margin-top: 2rem; }

  /* Utility */
  .center { display:flex; align-items:center; justify-content:center; }
  .mb-0{ margin-bottom:0; } .mb-2{ margin-bottom:.5rem; } .mb-3{ margin-bottom:1rem; } .mb-4{ margin-bottom:1.25rem; }
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
    st.markdown('<div class="center mb-2">' + logo_path.read_text() + '</div>', unsafe_allow_html=True)
else:
    st.markdown('<h1 class="center mb-0">FluxPricer AI</h1>', unsafe_allow_html=True)

# Main title
st.markdown('<h1>Real-time Dynamic Pricing for Fashion & Accessories</h1>', unsafe_allow_html=True)

# ✅ Show robot image (center + larger)
robot_path = pathlib.Path("assets/robo.png")
if robot_path.exists():
    st.image(str(robot_path), width=560)


# Subtitle
st.markdown(
    '<p style="margin-top:0.5rem; opacity:.9;">Multi-agent system delivering intelligent pricing decisions with real-time market adaptation</p>',
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)


# ————————————————————————————————————————————————————————————————
# Agents Grid
# ————————————————————————————————————————————————————————————————
st.markdown("## 🤖 Our Intelligent Agent System")
st.caption("Four specialized AI agents working in harmony to optimize your pricing strategy")

c1, c2, c3, c4 = st.columns(4, gap="large")
with c1:
    st.markdown('<div class="card lift agent-card"><div class="icon">📊</div><h4>Market Data Collector</h4><p>Gathers and preprocesses competitor pricing, sales history, and external market signals in real time.</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="card lift agent-card"><div class="icon">🤖</div><h4>Price Optimizer</h4><p>ML models and constrained optimization converge on ideal prices across products and regions.</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="card lift agent-card"><div class="icon">🔔</div><h4>Alert Agent</h4><p>Monitors market shocks and notifies you of opportunities or risks instantly.</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="card lift agent-card"><div class="icon">👤</div><h4>User Interaction</h4><p>Intuitive dashboards, clear explanations of model decisions, and safe manual overrides.</p></div>', unsafe_allow_html=True)

# ————————————————————————————————————————————————————————————————
# Primary Actions
# ————————————————————————————————————————————————————————————————
st.markdown("##Get Started")
a1, a2, a3 = st.columns(3, gap="large")

if st.session_state.get("session"):
    with a1:
        st.markdown('<div class="card lift"><div class="kicker">Navigation</div>', unsafe_allow_html=True)
        if st.button("Alerts & Notifications", key="btn_alerts"):
            st.switch_page("pages/5_Alerts_and_Notifications.py")
        st.markdown('</div>', unsafe_allow_html=True)

    with a2:
        st.markdown('<div class="card lift"><div class="kicker">Account</div>', unsafe_allow_html=True)
        if st.button("Profile", key="btn_profile"):
            st.switch_page("pages/4_Profile.py")
        st.markdown('</div>', unsafe_allow_html=True)

    with a3:
        st.markdown('<div class="card lift"><div class="kicker">Session</div>', unsafe_allow_html=True)
        st.markdown('<div class="stButton btn-danger">', unsafe_allow_html=True)
        logout_clicked = st.button("Logout", key="logout_btn")
        st.markdown('</div></div>', unsafe_allow_html=True)
        if logout_clicked:
            st.session_state["confirm_logout"] = True

    # Logout confirmation modal
    if st.session_state.get("confirm_logout"):
        st.markdown('<div class="overlay"></div>', unsafe_allow_html=True)
        st.markdown('<div class="modal"><div class="content">', unsafe_allow_html=True)
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
        st.markdown('<div class="card lift"><div class="kicker">Welcome back</div>', unsafe_allow_html=True)
        if st.button("🔑 Login", key="btn_login"):
            st.switch_page("pages/1_Login.py")
        st.markdown('</div>', unsafe_allow_html=True)
    with a2:
        st.markdown('<div class="card lift"><div class="kicker">New here?</div>', unsafe_allow_html=True)
        st.markdown('<div class="stButton btn-secondary">', unsafe_allow_html=True)
        if st.button("✨ Create Account", key="btn_register"):
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
# Footer
# ————————————————————————————————————————————————————————————————
st.markdown('<div class="footer">FluxPricer AI © — demo for coursework. Not for production use.</div>', unsafe_allow_html=True)
