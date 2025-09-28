#!/usr/bin/env python3

"""
Test complete registration flow including backend functionality.
"""

import sqlite3
import hashlib
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from core.auth_service import register_user, authenticate, RegisterIn
from core.auth_db import SessionLocal, User

def test_registration_backend():
    """Test the registration backend functionality."""
    print("Testing Registration Backend")
    print("=" * 40)
    
    # Test registration
    print("\n1. Testing user registration...")
    try:
        # Create a test user
        test_email = "test_nav@example.com"
        test_password = "test_password_123"
        test_full_name = "Test User"
        
        # First, check if user already exists and clean up
        try:
            with SessionLocal() as db:
                existing_user = db.query(User).filter(User.email == test_email).first()
                if existing_user:
                    db.delete(existing_user)
                    db.commit()
                    print(f"Cleaned up existing test user: {test_email}")
        except:
            pass
        
        # Register the user
        register_input = RegisterIn(
            email=test_email,
            full_name=test_full_name,
            password=test_password
        )
        register_user(register_input)
        print(f"SUCCESS: User registration worked for: {test_email}")
            
    except Exception as e:
        print(f"FAIL: Registration test failed: {e}")
        assert False, f"Registration test failed: {e}"
    
    # Test login
    print("\n2. Testing user authentication...")
    try:
        user_info = authenticate(test_email, test_password)
        
        if user_info and user_info.get("email") == test_email:
            print(f"SUCCESS: Authentication worked for user: {test_email}")
        else:
            print(f"FAIL: Authentication failed for user: {test_email}")
            assert False, f"Authentication failed for user: {test_email}"
            
    except Exception as e:
        print(f"FAIL: Authentication test failed: {e}")
        assert False, f"Authentication test failed: {e}"
        
    # Clean up
    print("\n3. Cleaning up test data...")
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == test_email).first()
            if user:
                db.delete(user)
                db.commit()
                print("SUCCESS: Test data cleaned up")
    except Exception as e:
        print(f"WARNING: Could not clean up test data: {e}")
    
    print("\nAll backend tests passed!")

if __name__ == "__main__":
    success = test_registration_backend()
    exit(0 if success else 1)