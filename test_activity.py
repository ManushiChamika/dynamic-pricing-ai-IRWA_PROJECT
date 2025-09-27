#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the current directory to Python path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Set environment variable
os.environ['TRACE_STEPS'] = '1'

try:
    from core.agents.agent_sdk.activity_log import activity_log, should_trace
    print(f"should_trace(): {should_trace()}")
    print(f"activity_log exists: {activity_log is not None}")
    
    # Add test logs
    activity_log.log('TEST_AGENT', 'test_logging', 'completed', 'This is a test message')
    activity_log.log('PRICING_AGENT', 'price_optimization', 'completed', 'Optimized pricing for Dell laptop')
    
    # Check recent logs
    recent = activity_log.recent(10)
    print(f"Recent logs count: {len(recent)}")
    
    if recent:
        print("Recent logs:")
        for i, log in enumerate(recent):
            print(f"  {i+1}. {log}")
    else:
        print("No recent logs found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()