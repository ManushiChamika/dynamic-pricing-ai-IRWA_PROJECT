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
        # Test registration with a new user
        print("Testing registration with new user...")
        register_user(RegisterIn(
            email="newuser@example.com",
            full_name="New Test User",
            password="newpassword123"
        ))
        print("SUCCESS: New user registration successful!")
        
        # Test authentication with the new user
        print("Testing authentication with new user...")
        session = authenticate("newuser@example.com", "newpassword123")
        print(f"SUCCESS: New user authentication successful! Session: {session}")
        
        # Test authentication with existing user
        print("Testing authentication with existing user...")
        session = authenticate("test@example.com", "testpassword123")
        print(f"SUCCESS: Existing user authentication successful! Session: {session}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_registration()