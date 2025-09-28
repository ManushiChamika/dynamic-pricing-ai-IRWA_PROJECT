#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the current directory to Python path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Set environment variable
os.environ['TRACE_STEPS'] = '1'

print("Testing UI activity service...")

try:
    from app.ui.services.activity import recent, ensure_bus_bridge
    print("Successfully imported UI activity service")
    
    # Ensure bridge
    bridge_ok = ensure_bus_bridge()
    print(f"Bridge initialized: {bridge_ok}")
    
    # Get logs
    logs = recent(50)
    print(f"Found {len(logs)} activity logs")
    
    for i, log in enumerate(logs):
        print(f"  {i+1}. {log}")
        
except Exception as e:
    print(f"Error testing UI activity service: {e}")
    import traceback
    traceback.print_exc()

print("Done.")