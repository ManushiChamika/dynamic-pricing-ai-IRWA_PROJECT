#!/usr/bin/env python3
"""Test script to verify thread title generation for thread 658."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.routers.utils import generate_thread_title
from core.chat_db import update_thread, SessionLocal, Thread
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(name)s: %(message)s'
)

def get_thread_title(thread_id: int):
    """Get thread title from database."""
    with SessionLocal() as db:
        t = db.get(Thread, thread_id)
        return t.title if t else None

def main():
    thread_id = 658
    print(f"\n{'='*60}")
    print(f"Testing title generation for thread {thread_id}")
    print(f"{'='*60}\n")
    
    # Check current title
    old_title = get_thread_title(thread_id)
    if old_title is None:
        print(f"Thread {thread_id} not found!")
        return 1
    
    print(f"Current title: '{old_title}'")
    
    # Generate new title
    title = generate_thread_title(thread_id)
    
    print(f"\n{'='*60}")
    if title:
        print(f"SUCCESS: Generated title: '{title}'")
        
        # Update the thread title in database
        print(f"\nUpdating thread {thread_id} title in database...")
        update_thread(thread_id, title=title)
        
        # Verify the update
        new_title = get_thread_title(thread_id)
        if new_title == title:
            print(f"[OK] Database updated successfully!")
            print(f"  Old title: '{old_title}'")
            print(f"  New title: '{new_title}'")
        else:
            print(f"[FAIL] Database update failed!")
            print(f"  Expected: '{title}'")
            print(f"  Got: '{new_title}'")
    else:
        print(f"FAILED: No title generated")
    print(f"{'='*60}\n")
    
    return 0 if title else 1

if __name__ == "__main__":
    sys.exit(main())
