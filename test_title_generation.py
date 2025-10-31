#!/usr/bin/env python3
"""Test script to verify thread title generation for thread 658."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.routers.utils import generate_thread_title
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(name)s: %(message)s'
)

def main():
    thread_id = 658
    print(f"\n{'='*60}")
    print(f"Testing title generation for thread {thread_id}")
    print(f"{'='*60}\n")
    
    title = generate_thread_title(thread_id)
    
    print(f"\n{'='*60}")
    if title:
        print(f"SUCCESS: Generated title: '{title}'")
    else:
        print(f"FAILED: No title generated")
    print(f"{'='*60}\n")
    
    return 0 if title else 1

if __name__ == "__main__":
    sys.exit(main())
