#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the current directory to Python path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Set environment variable
os.environ['TRACE_STEPS'] = '1'

print("Generating sample activity for testing...")

try:
    from core.agents.agent_sdk.activity_log import activity_log, generate_trace_id
    
    # Generate a realistic trace that mimics a chat interaction
    trace_id = generate_trace_id()
    
    # Chat prompt started
    activity_log.log('Chat', 'prompt.start', 'in_progress', 'Processing prompt from user@example.com', {
        'trace_id': trace_id,
        'user': 'user@example.com',
        'prompt': 'optimize the price of Dell Laptop',
        'action': 'start'
    })
    
    # Tool call to price optimizer
    activity_log.log('LLM', 'tool_call.start', 'in_progress', 'Calling price_optimizer_tool', {
        'trace_id': trace_id,
        'tool_name': 'price_optimizer_tool',
        'action': 'start'
    })
    
    # Price optimization proposal generated
    activity_log.log('PriceOptimizer', 'proposal.generated', 'completed', 'Dell Laptop: $899 -> $849 (85.0% confidence)', {
        'trace_id': trace_id,
        'sku': 'Dell Laptop',
        'old_price': 899,
        'new_price': 849,
        'rationale': 'Price reduced due to competitive analysis showing 15% lower market rates',
        'confidence': 0.85,
        'algorithm': 'competitive_analysis'
    })
    
    # Tool call completed
    activity_log.log('LLM', 'tool_call.done', 'completed', 'Tool price_optimizer_tool completed (2341ms)', {
        'trace_id': trace_id,
        'tool_name': 'price_optimizer_tool',
        'action': 'done',
        'duration_ms': 2341,
        'error': False
    })
    
    # Chat prompt completed
    activity_log.log('Chat', 'prompt.done', 'completed', 'Response generated (2856ms)', {
        'trace_id': trace_id,
        'action': 'done',
        'duration_ms': 2856
    })
    
    # Add a couple more interactions for variety
    trace_id2 = generate_trace_id()
    
    activity_log.log('Alerts', 'price.anomaly', 'failed', 'SKU Dell-7134Pr', {
        'trace_id': trace_id2,
        'severity': 'crit',
        'title': 'Price anomaly detected',
        'sku': 'Dell-7134Pr',
        'rule_id': 'price_spike_detector',
        'message': 'Price increase >20% detected'
    })
    
    activity_log.log('Pricing', 'price.update', 'completed', 'Dell-7134Pr $1200->$999 by admin (manual)', {
        'trace_id': trace_id2,
        'sku': 'Dell-7134Pr',
        'old_price': 1200,
        'new_price': 999,
        'actor': 'admin',
        'algorithm': 'manual'
    })
    
    # Check how many logs we have
    logs = activity_log.recent(20)
    print(f"Generated {len(logs)} activity log entries")
    
    print("\nSample entries:")
    for i, log in enumerate(logs[:3]):
        print(f"  {i+1}. [{log['ts']}] {log['agent']} - {log['action']} ({log['status']})")
        print(f"     {log['message']}")
    
    print(f"\nNow you can navigate to:")
    print("1. Open http://localhost:8501 in your browser")
    print("2. Click '⚡ OPERATIONS' in the sidebar")
    print("3. Click the '📋 Activity' radio button")
    print("4. You should see the activity feed with trace logs!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("Done.")