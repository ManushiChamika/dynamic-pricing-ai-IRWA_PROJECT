#!/usr/bin/env python3

"""
Test script to verify navigation flow works correctly.
This simulates clicking through the authentication flow.
"""

import requests
import time
from urllib.parse import urljoin, urlparse, parse_qs

def test_navigation_flow():
    """Test the complete navigation flow."""
    base_url = "http://localhost:8502"
    session = requests.Session()
    
    print("Testing Navigation Flow")
    print("=" * 50)
    
    # Test 1: Landing Page Load
    print("\n1. Testing Landing Page Load...")
    try:
        response = session.get(base_url)
        if response.status_code == 200:
            content = response.text
            if "FluxPricer AI" in content and "Login" in content and "Register" in content:
                print("SUCCESS: Landing page loads correctly with navigation buttons")
            else:
                print("FAIL: Landing page missing expected content")
                return False
        else:
            print(f"FAIL: Landing page failed to load: {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: Error loading landing page: {e}")
        return False
    
    # Test 2: Navigate to Register Page
    print("\n2. Testing Navigation to Register Page...")
    try:
        register_url = f"{base_url}/?page=register"
        response = session.get(register_url)
        if response.status_code == 200:
            content = response.text
            if "Register" in content and "Create" in content:
                print("SUCCESS: Register page loads correctly")
            else:
                print("FAIL: Register page missing expected content")
                return False
        else:
            print(f"FAIL: Register page failed to load: {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: Error loading register page: {e}")
        return False
    
    # Test 3: Navigate to Login Page
    print("\n3. Testing Navigation to Login Page...")
    try:
        login_url = f"{base_url}/?page=login"
        response = session.get(login_url)
        if response.status_code == 200:
            content = response.text
            if "Login" in content and ("Username" in content or "Email" in content):
                print("SUCCESS: Login page loads correctly")
            else:
                print("FAIL: Login page missing expected content")
                return False
        else:
            print(f"FAIL: Login page failed to load: {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: Error loading login page: {e}")
        return False
    
    # Test 4: Test Back to Landing
    print("\n4. Testing Navigation Back to Landing...")
    try:
        landing_url = f"{base_url}/?page=landing"
        response = session.get(landing_url)
        if response.status_code == 200:
            content = response.text
            if "FluxPricer AI" in content and "Enter Dashboard" in content:
                print("SUCCESS: Can navigate back to landing page")
            else:
                print("FAIL: Landing page navigation failed")
                return False
        else:
            print(f"FAIL: Landing page navigation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: Error navigating back to landing: {e}")
        return False
    
    print("\nAll navigation tests passed!")
    return True

if __name__ == "__main__":
    success = test_navigation_flow()
    exit(0 if success else 1)