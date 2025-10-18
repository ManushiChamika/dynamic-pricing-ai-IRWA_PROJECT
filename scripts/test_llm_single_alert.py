import asyncio
import sys
import pathlib
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.agents.alert_service.repo import Repo
from core.agents.alert_service.engine import AlertEngine
from core.agents.alert_service.schemas import PriceProposal
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic

bus = get_bus()

async def test_single_anomaly():
    print("\n" + "="*60)
    print("SINGLE LLM ALERT TEST - EXTREME ANOMALY")
    print("="*60)
    
    repo = Repo("app/alert.db")
    await repo.init()
    
    engine = AlertEngine(repo)
    
    event_received = asyncio.Event()
    original_on_pp = engine.on_pp
    
    async def on_pp_wrapper(pp):
        print(f"\n[DEBUG] AlertEngine received event: {pp}")
        event_received.set()
        await original_on_pp(pp)
    
    engine.on_pp = on_pp_wrapper
    
    await engine.start()
    
    print(f"\nLLM Available: {engine.llm.is_available() if engine.llm else False}")
    if engine.llm and engine.llm.is_available():
        print(f"Provider: {engine.llm.provider()}")
    
    print("\nInitial alerts in DB:")
    initial_incidents = await repo.list_incidents(status=None)
    print(f"  Total incidents: {len(initial_incidents)}")
    
    print("\nPublishing EXTREME anomaly event:")
    print("  - SKU: TEST-EXTREME")
    print("  - Proposed price: 5000.00")
    print("  - Margin: 2% (critically low)")
    
    extreme_proposal = PriceProposal(
        sku="TEST-EXTREME",
        proposed_price=5000.00,
        margin=0.02,
        ts=datetime.now(timezone.utc)
    )
    
    await bus.publish(Topic.PRICE_PROPOSAL, extreme_proposal)
    
    print("\nWaiting for LLM processing (10 seconds)...")
    await asyncio.sleep(10)
    
    print("\nChecking for LLM-created alerts...")
    all_incidents = await repo.list_incidents(status=None)
    llm_alerts = [inc for inc in all_incidents if inc.get("rule_id") == "llm_agent"]
    
    print(f"\nResults:")
    print(f"  Total incidents after: {len(all_incidents)}")
    print(f"  LLM-created alerts: {len(llm_alerts)}")
    
    if llm_alerts:
        print("\n  LLM Alert Details:")
        for alert in llm_alerts:
            print(f"    - ID: {alert.get('id')}")
            print(f"      Title: {alert.get('title')}")
            print(f"      Severity: {alert.get('severity')}")
            print(f"      Status: {alert.get('status')}")
    else:
        print("\n  No LLM alerts created (may be due to rate limiting)")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_single_anomaly())
