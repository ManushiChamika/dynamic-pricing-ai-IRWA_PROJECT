import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from core.agents.price_optimizer.agent import PricingOptimizerAgent
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic

async def main():
    print("=" * 70)
    print("END-TO-END PIPELINE TEST: Data Collector -> Price Optimizer -> Alert")
    print("=" * 70)
    
    bus = get_bus()
    
    price_proposals = []
    alerts_received = []
    
    async def track_proposal(payload):
        print(f"\n[EVENT] price.proposal received:")
        print(f"   product_id: {payload.get('product_id')}")
        print(f"   previous_price: ${payload.get('previous_price')}")
        print(f"   proposed_price: ${payload.get('proposed_price')}")
        price_proposals.append(payload)
    
    async def track_alert(alert):
        title = getattr(alert, 'title', str(alert))
        severity = getattr(alert, 'severity', 'unknown')
        print(f"\n[EVENT] ALERT received:")
        print(f"   title: {title}")
        print(f"   severity: {severity}")
        alerts_received.append(alert)
    
    print("\n[1] Setting up event monitoring...")
    bus.subscribe(Topic.PRICE_PROPOSAL.value, track_proposal)
    bus.subscribe(Topic.ALERT.value, track_alert)
    print("   Listening to: price.proposal, alert")
    
    print("\n[2] Starting Price Optimizer workflow...")
    optimizer = PricingOptimizerAgent()
    
    result = await optimizer.process_full_workflow(
        user_request="Optimize price to maximize profit",
        product_name="LAPTOP-001"
    )
    
    print(f"\n[3] Price Optimizer completed:")
    print(f"   Status: {result.get('status')}")
    print(f"   Product: {result.get('inputs', {}).get('title')}")
    print(f"   Algorithm: {result.get('algorithm')}")
    print(f"   Previous: ${result.get('inputs', {}).get('our_price')}")
    print(f"   Proposed: ${result.get('recommended_price')}")
    
    print("\n[4] Waiting for Alert Agent to react (5 seconds)...")
    await asyncio.sleep(5)
    
    print("\n" + "=" * 70)
    print("PIPELINE VERIFICATION")
    print("=" * 70)
    
    print(f"\n[STEP 1] Price Optimizer -> Event Bus")
    if price_proposals:
        print(f"   [PASS] {len(price_proposals)} price.proposal event(s) published")
    else:
        print("   [FAIL] No price.proposal events detected")
    
    print(f"\n[STEP 2] Event Bus -> Alert Agent")
    if alerts_received:
        print(f"   [PASS] {len(alerts_received)} alert(s) created by Alert Agent")
        print("\n   Alerts created:")
        for idx, alert in enumerate(alerts_received, 1):
            title = getattr(alert, 'title', str(alert))
            print(f"   {idx}. {title}")
    else:
        print("   [INFO] No alerts created")
        print("   (Alert Agent may be running but didn't detect anomalies,")
        print("    or LLM evaluation is not triggering alerts)")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if price_proposals and alerts_received:
        print("\n[SUCCESS] Full pipeline operational!")
        print("  Price Optimizer -> Event Bus -> Alert Agent (with LLM)")
        return 0
    elif price_proposals:
        print("\n[PARTIAL] Price Optimizer works, but Alert Agent not reacting")
        print("  Possible issues:")
        print("  - Alert Engine not started (run full backend)")
        print("  - LLM not invoking create_alert tool")
        print("  - Event subscription not working")
        return 1
    else:
        print("\n[FAIL] Price Optimizer not publishing events")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
