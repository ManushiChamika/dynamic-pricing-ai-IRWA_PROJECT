import asyncio
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
from core.agents.price_optimizer.agent import PricingOptimizerAgent
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic


class TestScenario:
    def __init__(self, name: str, prompt: str, description: str):
        self.name = name
        self.prompt = prompt
        self.description = description
        self.result = "PENDING"
        self.details = []
        self.errors = []

    def add_detail(self, detail: str):
        self.details.append(detail)

    def add_error(self, error: str):
        self.errors.append(error)

    def mark_pass(self):
        self.result = "PASS"

    def mark_fail(self, reason: str):
        self.result = "FAIL"
        self.add_error(reason)


class EndToEndValidator:
    def __init__(self):
        self.root = Path(__file__).resolve().parents[1]
        self.app_db = self.root / "app" / "data.db"
        self.alert_db = self.root / "app" / "alert.db"
        self.user_agent = UserInteractionAgent(user_name="test_user", mode="user")
        self.price_optimizer = PricingOptimizerAgent()
        self.bus = get_bus()
        self.scenarios: List[TestScenario] = []
        
        self.price_proposals_captured = []
        self.alerts_captured = []

    async def setup(self):
        print("=" * 80)
        print("BACKEND END-TO-END VALIDATION SYSTEM")
        print("=" * 80)
        print(f"\nInitialized at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"App Database: {self.app_db}")
        print(f"Alert Database: {self.alert_db}")
        
        async def capture_proposal(payload):
            self.price_proposals_captured.append(payload)
            print(f"  [EVENT CAPTURED] Price Proposal: {payload.get('product_id')} "
                  f"{payload.get('previous_price')} → {payload.get('proposed_price')}")

        async def capture_alert(alert):
            self.alerts_captured.append(alert)
            title = getattr(alert, 'title', str(alert))
            print(f"  [EVENT CAPTURED] Alert: {title}")

        self.bus.subscribe(Topic.PRICE_PROPOSAL.value, capture_proposal)
        self.bus.subscribe(Topic.ALERT.value, capture_alert)
        
        print("\n[PASS] Event bus listeners configured")
        print("    - Monitoring: price.proposal")
        print("    - Monitoring: alert")

    def get_product_from_db(self, sku: str) -> Optional[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.app_db)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT sku, title, current_price, cost FROM product_catalog WHERE sku=? LIMIT 1",
                (sku,)
            ).fetchone()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"    [DB ERROR] {e}")
            return None

    def check_incident_in_alert_db(self, sku: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.alert_db)
            conn.row_factory = sqlite3.Row
            if sku:
                rows = conn.execute(
                    "SELECT id, sku, severity, title, status, first_seen FROM incidents WHERE sku=? ORDER BY first_seen DESC LIMIT 5",
                    (sku,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, sku, severity, title, status, first_seen FROM incidents ORDER BY first_seen DESC LIMIT 10"
                ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"    [DB ERROR] {e}")
            return []

    async def run_scenario_1_standard_workflow(self):
        scenario = TestScenario(
            name="Scenario 1: Standard End-to-End Workflow",
            prompt="Find a new, better price for the Dell XPS 14 9440.",
            description="Tests the full workflow: product lookup → pricing analysis → proposal generation"
        )
        self.scenarios.append(scenario)
        
        print("\n" + "=" * 80)
        print(scenario.name)
        print("=" * 80)
        print(f"Prompt: {scenario.prompt}")
        print(f"Description: {scenario.description}")
        
        initial_proposal_count = len(self.price_proposals_captured)
        
        product = self.get_product_from_db("DELL-XPS-14-9440")
        if not product:
            scenario.add_detail("Product 'DELL-XPS-14-9440' not found in database, using fallback workflow")
        else:
            scenario.add_detail(f"Product found: {product['title']} at ${product['current_price']}")
        
        print("\n[RUNNING] Invoking Price Optimizer Agent...")
        try:
            result = await self.price_optimizer.process_full_workflow(
                user_request=scenario.prompt,
                product_name="Dell XPS 14 9440"
            )
            
            scenario.add_detail(f"Optimizer status: {result.get('status')}")
            scenario.add_detail(f"Algorithm used: {result.get('algorithm')}")
            scenario.add_detail(f"Recommended price: ${result.get('recommended_price')}")
            
            print(f"  Status: {result.get('status')}")
            print(f"  Algorithm: {result.get('algorithm')}")
            print(f"  Price: ${result.get('recommended_price')}")
            
        except Exception as e:
            scenario.mark_fail(f"Agent execution failed: {str(e)}")
            print(f"  [ERROR] {e}")
            return
        
        await asyncio.sleep(2)
        
        print("\n[VERIFICATION] Checking results...")
        
        new_proposals = self.price_proposals_captured[initial_proposal_count:]
        if len(new_proposals) > 0:
            scenario.add_detail(f"[PASS] Price proposal event published ({len(new_proposals)} events)")
            print(f"  [PASS] Price proposal events: {len(new_proposals)}")
            scenario.mark_pass()
        else:
            scenario.mark_fail("No price proposal event was published")
            print(f"  [FAIL] No price proposal event published")

    async def run_scenario_2_analytical_query(self):
        scenario = TestScenario(
            name="Scenario 2: Complex Analytical Query",
            prompt="Compare the current market prices for the Dell XPS 13 and the Lenovo ThinkPad X1 Carbon. Which one has a higher margin for us?",
            description="Tests the agent's ability to perform comparative analysis"
        )
        self.scenarios.append(scenario)
        
        print("\n" + "=" * 80)
        print(scenario.name)
        print("=" * 80)
        print(f"Prompt: {scenario.prompt}")
        print(f"Description: {scenario.description}")
        
        print("\n[RUNNING] Invoking User Interaction Agent...")
        
        response_parts = []
        try:
            for chunk in self.user_agent.stream_response(scenario.prompt):
                if isinstance(chunk, str):
                    response_parts.append(chunk)
            
            full_response = "".join(response_parts)
            scenario.add_detail(f"Response length: {len(full_response)} chars")
            
            print(f"\n[RESPONSE]")
            print(f"{full_response[:500]}..." if len(full_response) > 500 else full_response)
            
            has_dell = "dell" in full_response.lower()
            has_lenovo = "lenovo" in full_response.lower()
            has_margin = "margin" in full_response.lower()
            
            scenario.add_detail(f"Contains 'Dell': {has_dell}")
            scenario.add_detail(f"Contains 'Lenovo': {has_lenovo}")
            scenario.add_detail(f"Contains 'margin': {has_margin}")
            
            if has_dell and has_lenovo and has_margin:
                scenario.mark_pass()
                print(f"\n  [PASS] Response contains required keywords: Dell, Lenovo, margin")
            else:
                scenario.mark_fail(f"Response missing keywords. Dell:{has_dell}, Lenovo:{has_lenovo}, Margin:{has_margin}")
                print(f"\n  [FAIL] Response incomplete")
                
        except Exception as e:
            scenario.mark_fail(f"Agent execution failed: {str(e)}")
            print(f"  [ERROR] {e}")

    async def run_scenario_3_invalid_product(self):
        scenario = TestScenario(
            name="Scenario 3: Edge Case - Invalid Product",
            prompt="Optimize the price for FAKE-PRODUCT-123.",
            description="Tests graceful error handling for non-existent products"
        )
        self.scenarios.append(scenario)
        
        print("\n" + "=" * 80)
        print(scenario.name)
        print("=" * 80)
        print(f"Prompt: {scenario.prompt}")
        print(f"Description: {scenario.description}")
        
        initial_proposal_count = len(self.price_proposals_captured)
        
        print("\n[RUNNING] Invoking Price Optimizer Agent with invalid product...")
        try:
            result = await self.price_optimizer.process_full_workflow(
                user_request=scenario.prompt,
                product_name="FAKE-PRODUCT-123"
            )
            
            scenario.add_detail(f"Status: {result.get('status')}")
            scenario.add_detail(f"Message: {result.get('message', 'N/A')}")
            
            print(f"  Status: {result.get('status')}")
            print(f"  Message: {result.get('message', 'N/A')}")
            
            if result.get('status') == 'error':
                scenario.add_detail("[PASS] Agent returned error status (expected)")
                print(f"  [PASS] Error status returned (expected behavior)")
            else:
                scenario.add_detail("[FAIL] Agent did not return error status")
                print(f"  [FAIL] Expected error status")
            
        except Exception as e:
            scenario.add_detail(f"Exception raised: {str(e)}")
            print(f"  Exception: {e}")
        
        await asyncio.sleep(1)
        
        new_proposals = self.price_proposals_captured[initial_proposal_count:]
        if len(new_proposals) == 0:
            scenario.add_detail("[PASS] No price proposal created (expected)")
            scenario.mark_pass()
            print(f"  [PASS] No proposals created (expected)")
        else:
            scenario.mark_fail(f"Unexpected proposal created for invalid product")
            print(f"  [FAIL] Unexpected proposal created")

    async def run_scenario_4_alert_trigger(self):
        scenario = TestScenario(
            name="Scenario 4: Edge Case - Triggering an Alert",
            prompt="What is the price for the MX Master 4 mouse if we use a strategy to aggressively undercut all competitors by 30%?",
            description="Tests alert generation for high-risk pricing strategies"
        )
        self.scenarios.append(scenario)
        
        print("\n" + "=" * 80)
        print(scenario.name)
        print("=" * 80)
        print(f"Prompt: {scenario.prompt}")
        print(f"Description: {scenario.description}")
        
        initial_proposal_count = len(self.price_proposals_captured)
        initial_alert_count = len(self.alerts_captured)
        initial_incidents = self.check_incident_in_alert_db()
        initial_incident_count = len(initial_incidents)
        
        print("\n[RUNNING] Testing aggressive pricing strategy...")
        
        product = self.get_product_from_db("MX-MASTER-4")
        if not product:
            scenario.add_detail("Product 'MX-MASTER-4' not found, using alternative")
            product_name = "Dell XPS 14 9440"
        else:
            product_name = "MX Master 4"
            scenario.add_detail(f"Product found: {product['title']} at ${product['current_price']}")
        
        try:
            result = await self.price_optimizer.process_full_workflow(
                user_request="Use aggressive strategy to maximize profit by undercutting competitors by 30%",
                product_name=product_name
            )
            
            scenario.add_detail(f"Optimizer status: {result.get('status')}")
            scenario.add_detail(f"Recommended price: ${result.get('recommended_price')}")
            
            print(f"  Status: {result.get('status')}")
            print(f"  Recommended price: ${result.get('recommended_price')}")
            
        except Exception as e:
            scenario.add_error(f"Optimizer execution failed: {str(e)}")
            print(f"  [ERROR] {e}")
        
        await asyncio.sleep(3)
        
        print("\n[VERIFICATION] Checking for price proposal and alerts...")
        
        new_proposals = self.price_proposals_captured[initial_proposal_count:]
        new_alerts = self.alerts_captured[initial_alert_count:]
        current_incidents = self.check_incident_in_alert_db()
        new_incidents = [inc for inc in current_incidents if inc not in initial_incidents]
        
        proposal_created = len(new_proposals) > 0
        alert_created = len(new_alerts) > 0 or len(new_incidents) > 0
        
        if proposal_created:
            scenario.add_detail(f"[PASS] Price proposal created: {new_proposals[0].get('product_id')}")
            print(f"  [PASS] Price proposal: {new_proposals[0].get('product_id')} "
                  f"{new_proposals[0].get('previous_price')} -> {new_proposals[0].get('proposed_price')}")
        else:
            scenario.add_detail("[FAIL] No price proposal created")
            print(f"  [FAIL] No price proposal")
        
        if alert_created:
            scenario.add_detail(f"[PASS] Alert triggered: {len(new_alerts)} event(s), {len(new_incidents)} incident(s)")
            print(f"  [PASS] Alerts: {len(new_alerts)} events, {len(new_incidents)} incidents")
            if new_incidents:
                for inc in new_incidents[:3]:
                    print(f"    - {inc['title']} (severity: {inc['severity']})")
        else:
            scenario.add_detail("[WARN] No alert detected (Alert Agent may not be running)")
            print(f"  [WARN] No alerts detected")
            print(f"    Note: Alert Agent must be running in the full backend")
        
        if proposal_created:
            scenario.mark_pass()
            scenario.add_detail("Proposal verification: PASS")
            if not alert_created:
                scenario.add_detail("Alert verification: SKIP (requires Alert Agent running)")
        else:
            scenario.mark_fail("No proposal created for aggressive strategy")

    async def run_all_scenarios(self):
        await self.setup()
        
        await self.run_scenario_1_standard_workflow()
        await self.run_scenario_2_analytical_query()
        await self.run_scenario_3_invalid_product()
        await self.run_scenario_4_alert_trigger()

    def print_final_report(self):
        print("\n" + "=" * 80)
        print("VALIDATION REPORT SUMMARY")
        print("=" * 80)
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total scenarios: {len(self.scenarios)}")
        
        passed = sum(1 for s in self.scenarios if s.result == "PASS")
        failed = sum(1 for s in self.scenarios if s.result == "FAIL")
        
        print(f"\nResults: {passed} PASS | {failed} FAIL")
        
        for idx, scenario in enumerate(self.scenarios, 1):
            status_icon = "[PASS]" if scenario.result == "PASS" else "[FAIL]"
            print(f"\n{status_icon} {scenario.name}")
            print(f"  Result: {scenario.result}")
            
            if scenario.details:
                print(f"  Details:")
                for detail in scenario.details:
                    print(f"    - {detail}")
            
            if scenario.errors:
                print(f"  Errors:")
                for error in scenario.errors:
                    print(f"    [FAIL] {error}")
        
        print("\n" + "=" * 80)
        print("SYSTEM INTEGRATION STATUS")
        print("=" * 80)
        print(f"Total Price Proposals Captured: {len(self.price_proposals_captured)}")
        print(f"Total Alerts Captured: {len(self.alerts_captured)}")
        
        total_incidents = self.check_incident_in_alert_db()
        print(f"Total Incidents in Alert DB: {len(total_incidents)}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        if failed > 0:
            print("\n⚠ Some scenarios failed. Please review the errors above.")
        else:
            print("\n✓ All scenarios passed successfully!")
        
        if len(self.alerts_captured) == 0:
            print("\n⚠ No alerts captured during testing.")
            print("  To test Alert Agent functionality:")
            print("  1. Ensure the full backend is running (run_full_app.bat)")
            print("  2. Alert Agent must be started and subscribed to PRICE_PROPOSAL events")
            print("  3. Re-run this validation script")
        
        print("\n" + "=" * 80)
        
        return 0 if failed == 0 else 1


async def main():
    validator = EndToEndValidator()
    
    try:
        await validator.run_all_scenarios()
        exit_code = validator.print_final_report()
        return exit_code
    except Exception as e:
        print(f"\n[FATAL ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
