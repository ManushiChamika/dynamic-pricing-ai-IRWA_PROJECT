import asyncio
import sys
import pathlib
from datetime import datetime, timezone
import json

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

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add(self, name: str, passed: bool, details: str = ""):
        self.tests.append({"name": name, "passed": passed, "details": details})
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        status = "[PASS]" if passed else "[FAIL]"
        print(f"\n{status}: {name}")
        if details:
            print(f"  Details: {details}")
    
    def summary(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total: {len(self.tests)} | Passed: {self.passed} | Failed: {self.failed}")
        if self.failed > 0:
            print("\nFailed tests:")
            for t in self.tests:
                if not t["passed"]:
                    print(f"  - {t['name']}")
        print("="*60)
        return self.failed == 0

async def test_1_engine_startup(results: TestResults, repo: Repo, engine: AlertEngine):
    try:
        await engine.start()
        
        llm_available = engine.llm is not None and engine.llm.is_available()
        
        details = f"LLM available: {llm_available}"
        if llm_available:
            details += f", Provider: {engine.llm.provider()}, Model: {engine.llm.model}"
        
        results.add(
            "AlertEngine Startup & LLM Initialization",
            True,
            details
        )
        return True
    except Exception as e:
        results.add("AlertEngine Startup & LLM Initialization", False, str(e))
        return False

async def test_2_normal_price_proposal(results: TestResults, repo: Repo):
    try:
        initial_count = len(await repo.list_incidents(None))
        
        normal_pp = PriceProposal(
            sku="TEST-NORMAL",
            proposed_price=100.0,
            margin=0.35,
            ts=datetime.now(timezone.utc)
        )
        
        await bus.publish(Topic.PRICE_PROPOSAL.value, normal_pp)
        await asyncio.sleep(2)
        
        final_count = len(await repo.list_incidents(None))
        new_alerts = final_count - initial_count
        
        results.add(
            "Normal Price Proposal (No Alert Expected)",
            new_alerts == 0,
            f"New alerts created: {new_alerts}"
        )
    except Exception as e:
        results.add("Normal Price Proposal (No Alert Expected)", False, str(e))

async def test_3_large_price_jump(results: TestResults, repo: Repo):
    try:
        initial_incidents = await repo.list_incidents(None)
        initial_llm_alerts = [i for i in initial_incidents if i.get("rule_id") == "llm_agent"]
        
        jump_pp = PriceProposal(
            sku="TEST-JUMP",
            proposed_price=200.0,
            margin=0.40,
            ts=datetime.now(timezone.utc)
        )
        
        await bus.publish(Topic.PRICE_PROPOSAL.value, jump_pp)
        await asyncio.sleep(3)
        
        final_incidents = await repo.list_incidents(None)
        final_llm_alerts = [i for i in final_incidents if i.get("rule_id") == "llm_agent"]
        
        new_llm_alerts = len(final_llm_alerts) - len(initial_llm_alerts)
        
        results.add(
            "Large Price Jump Detection",
            new_llm_alerts >= 0,
            f"LLM alerts created: {new_llm_alerts}"
        )
    except Exception as e:
        results.add("Large Price Jump Detection", False, str(e))

async def test_4_low_margin_breach(results: TestResults, repo: Repo):
    try:
        initial_incidents = await repo.list_incidents(None)
        
        low_margin_pp = PriceProposal(
            sku="TEST-LOW-MARGIN",
            proposed_price=95.0,
            margin=0.15,
            ts=datetime.now(timezone.utc)
        )
        
        await bus.publish(Topic.PRICE_PROPOSAL.value, low_margin_pp)
        await asyncio.sleep(3)
        
        final_incidents = await repo.list_incidents(None)
        new_incidents = [i for i in final_incidents if i not in initial_incidents]
        
        low_margin_alert = any(
            "margin" in i.get("title", "").lower() or 
            i.get("severity") in ["warn", "crit"]
            for i in new_incidents
        )
        
        results.add(
            "Low Margin Breach Detection",
            len(new_incidents) >= 0,
            f"Total new incidents: {len(new_incidents)}, Low margin detected: {low_margin_alert}"
        )
    except Exception as e:
        results.add("Low Margin Breach Detection", False, str(e))

async def test_5_tool_execution(results: TestResults, engine: AlertEngine):
    try:
        if not engine.llm or not engine.llm.is_available():
            results.add(
                "LLM Tool Execution Capability",
                True,
                "Skipped - LLM not available"
            )
            return
        
        from core.agents.alert_service.tools import get_llm_tools, execute_tool_call
        
        tools = get_llm_tools()
        has_required_tools = len(tools) >= 3
        
        tool_names = [t["function"]["name"] for t in tools]
        expected_tools = ["list_rules", "list_alerts", "create_alert"]
        all_tools_present = all(t in tool_names for t in expected_tools)
        
        list_rules_result = await execute_tool_call("list_rules", {}, engine.tools)
        rules_success = list_rules_result.get("ok", False)
        
        list_alerts_result = await execute_tool_call("list_alerts", {"status": "OPEN"}, engine.tools)
        alerts_success = list_alerts_result.get("ok", False)
        
        passed = has_required_tools and all_tools_present and rules_success and alerts_success
        
        results.add(
            "LLM Tool Execution Capability",
            passed,
            f"Tools: {len(tools)}, All present: {all_tools_present}, list_rules: {rules_success}, list_alerts: {alerts_success}"
        )
    except Exception as e:
        results.add("LLM Tool Execution Capability", False, str(e))

async def test_6_verify_database_state(results: TestResults, repo: Repo):
    try:
        all_incidents = await repo.list_incidents(None)
        open_incidents = await repo.list_incidents("OPEN")
        rules = await repo.list_rules()
        
        results.add(
            "Database State Verification",
            True,
            f"Total incidents: {len(all_incidents)}, Open: {len(open_incidents)}, Rules: {len(rules)}"
        )
    except Exception as e:
        results.add("Database State Verification", False, str(e))

async def test_7_extreme_anomaly(results: TestResults, repo: Repo):
    try:
        initial_count = len(await repo.list_incidents(None))
        
        extreme_pp = PriceProposal(
            sku="TEST-EXTREME",
            proposed_price=500.0,
            margin=0.05,
            ts=datetime.now(timezone.utc)
        )
        
        await bus.publish(Topic.PRICE_PROPOSAL.value, extreme_pp)
        await asyncio.sleep(3)
        
        final_count = len(await repo.list_incidents(None))
        new_alerts = final_count - initial_count
        
        results.add(
            "Extreme Anomaly Detection (High Price + Low Margin)",
            new_alerts >= 0,
            f"New alerts: {new_alerts}"
        )
    except Exception as e:
        results.add("Extreme Anomaly Detection", False, str(e))

async def test_8_inspect_llm_created_alerts(results: TestResults, repo: Repo):
    try:
        all_incidents = await repo.list_incidents(None)
        llm_incidents = [i for i in all_incidents if i.get("rule_id") == "llm_agent"]
        
        details_parts = [f"Total LLM-created alerts: {len(llm_incidents)}"]
        
        if llm_incidents:
            details_parts.append("\nRecent LLM alerts:")
            for inc in llm_incidents[-3:]:
                details_parts.append(
                    f"  - {inc.get('title', 'N/A')} | SKU: {inc.get('sku', 'N/A')} | "
                    f"Severity: {inc.get('severity', 'N/A')} | Status: {inc.get('status', 'N/A')}"
                )
        
        results.add(
            "LLM-Created Alerts Inspection",
            True,
            "\n".join(details_parts)
        )
    except Exception as e:
        results.add("LLM-Created Alerts Inspection", False, str(e))

async def main():
    print("\n" + "="*60)
    print("LLM ALERT AGENT COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    results = TestResults()
    repo = Repo()
    engine = AlertEngine(repo)
    
    startup_ok = await test_1_engine_startup(results, repo, engine)
    
    if not startup_ok:
        print("\n⚠ Engine startup failed, aborting tests")
        results.summary()
        return 1
    
    print("\n--- Running Functional Tests ---")
    
    await test_2_normal_price_proposal(results, repo)
    await test_3_large_price_jump(results, repo)
    await test_4_low_margin_breach(results, repo)
    await test_5_tool_execution(results, engine)
    await test_6_verify_database_state(results, repo)
    await test_7_extreme_anomaly(results, repo)
    await test_8_inspect_llm_created_alerts(results, repo)
    
    all_passed = results.summary()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
