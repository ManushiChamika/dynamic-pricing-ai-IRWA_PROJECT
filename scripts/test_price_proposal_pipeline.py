import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from core.agents.price_optimizer.agent import PricingOptimizerAgent
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic

async def main():
    print("=" * 60)
    print("PRICE PROPOSAL PIPELINE DIAGNOSTIC TEST")
    print("=" * 60)
    
    print("\n[1] Setting up event bus listener for price.proposal events...")
    bus = get_bus()
    
    received_proposals = []
    
    async def capture_proposal(payload):
        print(f"\n[SUCCESS] RECEIVED price.proposal event:")
        print(f"   proposal_id: {payload.get('proposal_id')}")
        print(f"   product_id: {payload.get('product_id')}")
        print(f"   previous_price: {payload.get('previous_price')}")
        print(f"   proposed_price: {payload.get('proposed_price')}")
        received_proposals.append(payload)
    
    bus.subscribe(Topic.PRICE_PROPOSAL.value, capture_proposal)
    print(f"   Subscribed to topic: {Topic.PRICE_PROPOSAL.value}")
    
    print("\n[2] Initializing PricingOptimizerAgent...")
    optimizer = PricingOptimizerAgent()
    print(f"   Using database: {optimizer.db.app_db}")
    print(f"   LLM Brain enabled: {optimizer.llm_brain is not None}")
    
    print("\n[3] Running pricing workflow for product 'LAPTOP-001' (Dell XPS 15)...")
    result = await optimizer.process_full_workflow(
        user_request="Optimize price to maximize profit",
        product_name="LAPTOP-001",
        wait_seconds=1,
        max_wait_attempts=1
    )
    
    print("\n[4] Pricing Workflow Result:")
    print(f"   Status: {result.get('status')}")
    print(f"   Product: {result.get('inputs', {}).get('title')}")
    print(f"   SKU: {result.get('inputs', {}).get('sku')}")
    print(f"   Previous Price: ${result.get('inputs', {}).get('our_price')}")
    print(f"   Recommended Price: ${result.get('recommended_price')}")
    print(f"   Algorithm: {result.get('algorithm')}")
    print(f"   Confidence: {result.get('confidence')}")
    print(f"   Reason: {result.get('reason')}")
    
    await asyncio.sleep(0.5)
    
    print("\n[5] Checking if price.proposal event was published...")
    if received_proposals:
        print(f"   [SUCCESS]: {len(received_proposals)} proposal(s) received")
        for idx, proposal in enumerate(received_proposals, 1):
            print(f"   Proposal {idx}: {proposal}")
    else:
        print("   [FAILURE]: No price.proposal events received")
        print("   This means the Price Optimizer is NOT publishing events to the bus!")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 60)
    
    if not received_proposals:
        print("\n[WARNING] ISSUE IDENTIFIED:")
        print("The Price Optimizer workflow completed but did not publish")
        print("a price.proposal event. This breaks the pipeline to Alert Agent.")
        return 1
    else:
        print("\n[SUCCESS] Pipeline working correctly!")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
