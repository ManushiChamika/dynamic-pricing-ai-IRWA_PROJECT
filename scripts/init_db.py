
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.chat_db import init_chat_db

if __name__ == "__main__":
    print("Initializing chat database...")
    init_chat_db()
    print("Database initialization complete.")
