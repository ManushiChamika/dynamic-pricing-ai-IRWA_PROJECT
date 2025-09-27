#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the project root to Python path
HERE = Path(__file__).resolve()
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from core.auth_service import register_user, authenticate, RegisterIn
from core.auth_db import init_db

def test_registration():
    print("Initializing database...")
    init_db()
    
    try:
        # Test registration with a completely fresh user
        import time
        timestamp = int(time.time())
        test_email = f"testuser{timestamp}@example.com"
        
        print(f"Testing registration with completely new user: {test_email}")
        register_user(RegisterIn(
            email=test_email,
            full_name="Test User",
            password="testpassword123"
        ))
        print("SUCCESS: New user registration successful!")
        
        # Test authentication with the new user
        print("Testing authentication with new user...")
        session = authenticate(test_email, "testpassword123")
        print(f"SUCCESS: New user authentication successful! Session: {session}")
        
        # Test authentication with wrong password
        print("Testing authentication with wrong password...")
        try:
            session = authenticate(test_email, "wrongpassword")
            print("ERROR: Authentication should have failed!")
        except ValueError as e:
            print(f"SUCCESS: Authentication correctly rejected wrong password: {e}")
        
        # Test duplicate registration
        print("Testing duplicate registration...")
        try:
            register_user(RegisterIn(
                email=test_email,
                full_name="Duplicate User",
                password="anotherpassword123"
            ))
            print("ERROR: Duplicate registration should have failed!")
        except ValueError as e:
            print(f"SUCCESS: Duplicate registration correctly rejected: {e}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_registration()