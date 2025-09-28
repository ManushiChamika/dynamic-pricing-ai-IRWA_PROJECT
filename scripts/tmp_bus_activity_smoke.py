#!/usr/bin/env python3
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from core.agents.agent_sdk import get_bus, Topic
from app.ui.services.activity import ensure_bus_bridge, recent

async def main():
    ensure_bus_bridge()
    bus = get_bus()
    # Publish a typed price.proposal event
    await bus.publish(Topic.PRICE_PROPOSAL.value, {
        'proposal_id': 'p1',
        'product_id': 'SKU-TEST',
        'previous_price': 100,
        'proposed_price': 90,
        'confidence': 0.82,
        'rationale': 'Test proposal'
    })
    # Publish market fetch ack/done events
    await bus.publish(Topic.MARKET_FETCH_ACK.value, {
        'request_id': 'r1', 'job_id': 'j1', 'status': 'RUNNING'
    })
    await bus.publish(Topic.MARKET_FETCH_DONE.value, {
        'request_id': 'r1', 'job_id': 'j1', 'status': 'DONE', 'tick_count': 3
    })
    # Print recent activities
    logs = recent(10)
    print(json.dumps(logs, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
