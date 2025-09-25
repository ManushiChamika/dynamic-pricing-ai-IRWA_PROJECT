#!/usr/bin/env python3
"""
Test UI Integration - Simple test to verify components work
"""
import sys
import pathlib

# Add project root to path
HERE = pathlib.Path(__file__).resolve()
PROJECT_ROOT = HERE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

def test_theme_import():
    """Test theme components"""
    try:
        from app.ui.theme.inject import apply_theme
        print("[OK] Theme injection import successful")
        
        from app.ui.theme import tokens
        print("[OK] Theme tokens import successful")
        return True
    except Exception as e:
        print(f"[ERROR] Theme import error: {e}")
        return False

def test_landing_import():
    """Test landing page"""
    try:
        from app.ui.views.landing import view as landing_view
        print("[OK] Landing page import successful")
        return True
    except Exception as e:
        print(f"[ERROR] Landing page import error: {e}")
        return False

def test_state_import():
    """Test state management"""
    try:
        from app.ui.state.session import require_session
        print("[OK] Session state import successful")
        return True
    except Exception as e:
        print(f"[ERROR] Session state import error: {e}")
        return False

if __name__ == "__main__":
    print("Testing UI Integration Components...")
    print("=" * 50)
    
    all_passed = True
    all_passed &= test_theme_import()
    all_passed &= test_landing_import()
    all_passed &= test_state_import()
    
    print("=" * 50)
    if all_passed:
        print("All tests passed! UI integration is ready.")
    else:
        print("Some tests failed. Check errors above.")
    
    print("To test in browser:")
    print("1. Run: streamlit run app/streamlit_app.py --server.port 8503")
    print("2. Visit: http://localhost:8503/?page=landing")