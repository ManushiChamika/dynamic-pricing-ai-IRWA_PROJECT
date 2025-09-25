# Minimal UI Test App - tests just the UI integration
import sys, pathlib

# Add project root to path
HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(page_title="FluxPricer AI - UI Test", page_icon="💹", layout="wide")

# Test basic UI routing
page = st.query_params.get("page", "home")

st.title("UI Integration Test")
st.write(f"Current page parameter: {page}")

if page == "landing":
    st.header("Testing New UI Landing Page")
    try:
        from app.ui.views.landing import view as landing_view
        landing_view()
        st.success("✅ Landing page rendered successfully!")
    except Exception as e:
        st.error(f"❌ Landing page error: {e}")
        st.code(str(e))
        
elif page == "theme":
    st.header("Testing Theme System")
    try:
        from app.ui.theme.inject import apply_theme
        apply_theme(False)  # Light theme
        st.success("✅ Theme applied successfully!")
        st.info("Theme has been applied to this page")
    except Exception as e:
        st.error(f"❌ Theme error: {e}")
        
else:
    st.info("Default test page")
    st.markdown("""
    ### Test the UI Integration:
    
    - **Landing Page**: [?page=landing](?page=landing)
    - **Theme Test**: [?page=theme](?page=theme)
    
    ### If tests pass, the UI integration is working!
    """)