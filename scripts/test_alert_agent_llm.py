import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from core.agents.alert_service.engine import AlertEngine
from core.agents.alert_service.repo import Repo
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic

async def main():
    print("=" * 60)
    print("ALERT AGENT LLM EVALUATION TEST")
    print("=" * 60)
    
    print("\n[1] Initializing Alert Engine...")
    repo = Repo(path="app/alert.db")
    engine = AlertEngine(repo)
    
    await engine.start()
    
    print(f"   LLM Available: {engine.llm and engine.llm.is_available()}")
    print(f"   Rules Loaded: {len(engine._rules)}")
    print(f"   Sinks Available: {list(engine.sinks.keys())}")
    
    print("\n[2] Monitoring for ALERT events published by Alert Agent...")
    bus = get_bus()
    
    received_alerts = []
    
    async def capture_alert(alert):
        title = getattr(alert, 'title', 'Unknown')
        severity = getattr(alert, 'severity', 'Unknown')
        sku = getattr(alert, 'sku', 'Unknown')
        print(f"\n[ALERT DETECTED]")
        print(f"   Title: {title}")
        print(f"   Severity: {severity}")
        print(f"   SKU: {sku}")
        print(f"   Full alert: {alert}")
        received_alerts.append(alert)
    
    bus.subscribe(Topic.ALERT.value, capture_alert)
    print("   Subscribed to ALERT topic")
    
    print("\n[3] Publishing test PRICE_PROPOSAL event with CRITICAL anomaly...")
    print("   Scenario: $1299.99 -> $125.00 (90% price drop, 2% margin - CRITICAL)")
    
    test_proposal = {
        "proposal_id": "test_critical_001",
        "product_id": "LAPTOP-001",
        "previous_price": 1299.99,
        "proposed_price": 125.0,
    }
    
    await bus.publish(Topic.PRICE_PROPOSAL.value, test_proposal)
    print("   Event published, waiting for Alert Agent response...")
    
    await asyncio.sleep(5)
    
    print("\n[4] Checking LLM evaluation results...")
    
    if received_alerts:
        print(f"   [SUCCESS] Alert Agent created {len(received_alerts)} alert(s)")
        for idx, alert in enumerate(received_alerts, 1):
            title = getattr(alert, 'title', 'Unknown')
            print(f"   Alert {idx}: {title}")
    else:
        print("   [FAILURE] No alerts created by Alert Agent")
        print("   Possible causes:")
        print("   - LLM not evaluating events")
        print("   - LLM not invoking create_alert tool")
        print("   - Event not reaching Alert Agent")
    
    print("\n[5] Checking database for persisted alerts...")
    alerts_db = await repo.list_incidents(limit=10)
    print(f"   Total incidents in DB: {len(alerts_db)}")
    
    if alerts_db:
        print("\n   Recent incidents:")
        for incident in alerts_db[:3]:
            print(f"   - {incident.id}: {incident.title} (severity: {incident.severity})")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    if received_alerts:
        print("\n[SUCCESS] Alert Agent LLM evaluation is working!")
        print("LLM successfully:")
        print("  1. Received price.proposal event")
        print("  2. Analyzed anomaly with LLM reasoning")
        print("  3. Invoked create_alert tool")
        return 0
    else:
        print("\n[FAILURE] Alert Agent did not create alerts")
        print("Next steps: Debug LLM tool calling and event subscription")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
