"""
UI Component Test Page - Testing individual UI components for safety
"""
import streamlit as st
import sys
import pathlib

# Add project root to path
HERE = pathlib.Path(__file__).resolve()
PROJECT_ROOT = HERE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

st.title("🧪 UI Component Test Page")
st.markdown("Testing individual UI components for safe integration")

# Test Theme Components
st.header("1. Theme Components")
try:
    from app.ui.theme.inject import apply_theme
    st.success("✅ Theme injection import successful")
    
    # Test apply theme
    apply_theme(False)  # Light theme
    st.success("✅ Theme application successful")
    
except Exception as e:
    st.error(f"❌ Theme error: {e}")

# Test Theme Tokens
try:
    from app.ui.theme import tokens
    st.success("✅ Theme tokens import successful")
except Exception as e:
    st.error(f"❌ Theme tokens error: {e}")

# Test State Components
st.header("2. State Components")
try:
    from app.ui.state.session import require_session
    st.success("✅ Session state import successful")
    # Don't actually call require_session as it might redirect
except Exception as e:
    st.error(f"❌ Session state error: {e}")

# Test Service Components (Critical - these likely have backend deps)
st.header("3. Service Components")

# Test Activity Service
try:
    from app.ui.services.activity import ensure_bus_bridge
    st.success("✅ Activity service import successful")
    st.warning("⚠️ Not testing ensure_bus_bridge() - backend dependency")
except Exception as e:
    st.error(f"❌ Activity service error: {e}")

# Test Alerts Service
try:
    from app.ui.services.alerts import list_incidents, list_rules
    st.success("✅ Alerts service import successful")
    st.warning("⚠️ Not testing actual functions - backend dependency")
except Exception as e:
    st.error(f"❌ Alerts service error: {e}")

# Test Runtime Service
try:
    from app.ui.services.runtime import ensure_bg_loop
    st.success("✅ Runtime service import successful")
except Exception as e:
    st.error(f"❌ Runtime service error: {e}")

# Test View Components (These are the main UI elements)
st.header("4. View Components")

views_to_test = [
    ("Landing", "app.ui.views.landing"),
    ("Dashboard", "app.ui.views.dashboard"), 
    ("Chat", "app.ui.views.chat"),
    ("Activity", "app.ui.views.activity_view"),
    ("Incidents", "app.ui.views.incidents"),
    ("Rules", "app.ui.views.rules"),
    ("Settings", "app.ui.views.settings")
]

for view_name, module_path in views_to_test:
    try:
        __import__(module_path)
        st.success(f"✅ {view_name} view import successful")
    except Exception as e:
        st.error(f"❌ {view_name} view error: {e}")

st.header("5. Test Simple View Rendering")
st.markdown("Testing if we can render simple views with dummy data...")

# Test Landing Page (should be most independent)
try:
    from app.ui.views import landing
    st.success("✅ Landing view module imported")
    
    # Create a test container for landing
    with st.expander("🧪 Test Landing Page Render"):
        try:
            landing.view()
            st.success("✅ Landing page rendered successfully!")
        except Exception as e:
            st.error(f"❌ Landing render error: {e}")
            st.text(str(e))
            
except Exception as e:
    st.error(f"❌ Could not test landing page: {e}")

st.markdown("---")
st.info("📋 **Next Steps**: Based on test results, identify which components are safe to copy first")