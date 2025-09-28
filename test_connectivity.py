#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the current directory to Python path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Set environment variable
os.environ['TRACE_STEPS'] = '1'

print("Testing activity log connectivity...")

# Test core activity log
try:
    from core.agents.agent_sdk.activity_log import activity_log as core_log, get_activity_log
    print("Imported core activity log")
    
    # Add test data to core log
    core_log.log('CORE_TEST', 'connectivity_test', 'completed', 'Testing core log connectivity')
    core_logs = core_log.recent(10)
    print(f"Core log has {len(core_logs)} items")
    
    # Test get_activity_log function
    get_log = get_activity_log()
    get_logs = get_log.recent(10)
    print(f"get_activity_log() returns {len(get_logs)} items")
    
    # Verify they're the same instance
    print(f"Same instance: {core_log is get_log}")
    
except Exception as e:
    print(f"Core log error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test UI service
try:
    from app.ui.services.activity import activity_log as ui_log, recent as ui_recent
    print("Imported UI activity service")
    
    # Check if UI sees the core logs
    ui_logs_direct = ui_log.recent(10) if ui_log else []
    ui_logs_func = ui_recent(10)
    
    print(f"UI activity_log.recent(): {len(ui_logs_direct)} items")
    print(f"UI recent() function: {len(ui_logs_func)} items")
    
    # Verify same instance
    if ui_log and core_log:
        print(f"UI and Core same instance: {ui_log is core_log}")
    
    if ui_logs_func:
        print("UI logs:")
        for log in ui_logs_func:
            print(f"  - {log}")
    
except Exception as e:
    print(f"UI log error: {e}")
    import traceback
    traceback.print_exc()

print("Done.")