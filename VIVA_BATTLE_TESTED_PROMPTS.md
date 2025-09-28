"""
VIVA DEMO BATTLE-TESTED PROMPTS
For Multi-Agent Dynamic Pricing AI System
STATUS: ✅ ALL AGENTS VERIFIED AND OPERATIONAL
UPDATED: Dec 2024 - Chat UI Enhanced with Agent Detection & Staged Bubbles

=== SIMPLE UIA-ONLY PROMPTS ===
These should be handled by User Interaction Agent alone:

1. "What brands do we have available?"
   Expected: Lists unique brands from database
   ✅ VERIFIED: Returns Dell, HP, ASUS, Razer, etc.

2. "How many products are in our catalog?"
   Expected: Count of total products  
   ✅ VERIFIED: Returns 20 products

3. "Show me all gaming laptops under 200,000 LKR"
   Expected: Filtered list with prices
   ✅ VERIFIED: Returns filtered results

4. "What is the most expensive laptop in our database?"
   Expected: Product with maximum price
   ✅ VERIFIED: Returns highest-priced item

5. "Show me Dell laptops only"
   Expected: Brand-filtered product list
   ✅ VERIFIED: Filters by brand correctly

=== COMPLEX POA-TRIGGERING PROMPTS ===
These should trigger UIA -> POA handoff with visible UI feedback:

1. "Optimize pricing strategy for gaming laptops using AI algorithms"
   Expected: UIA calls run_pricing_workflow, POA shows activity
   ✅ VERIFIED: Triggers POA workflow with UI feedback

2. "Maximize profit margins for HP laptops using advanced pricing algorithms"
   Expected: POA workflow with algorithm selection and optimization
   ✅ VERIFIED: Complex pricing analysis with margin optimization

3. "Use AI to set optimal prices for laptops considering market competition"
   Expected: Complex POA workflow with market context analysis
   ✅ VERIFIED: Multi-step pricing optimization

4. "Strategic pricing optimization for maximum revenue using machine learning"
   Expected: POA with ML algorithm selection
   ✅ VERIFIED: Advanced AI-driven pricing strategy

5. "Optimize all laptop prices for competitive advantage and profit maximization"
   Expected: Full POA workflow with business strategy analysis
   ✅ VERIFIED: Comprehensive pricing strategy workflow

=== ALERT AGENT SCENARIOS ===
These should trigger Alert & Notification Agent:

1. "Check for any critical pricing situations that need immediate attention"
   Expected: ANA scans for price alerts, margin breaches, competitor threats
   ✅ VERIFIED: scan_for_alerts tool triggers comprehensive alert check

2. "Alert me if any products have pricing issues or competitive threats"
   Expected: ANA monitors competitive positioning and margin issues
   ✅ VERIFIED: Multi-type alert detection (price drops, volatility, stock)

3. "Scan for pricing anomalies and margin breaches across all products"
   Expected: ANA detects market volatility and critical situations
   ✅ VERIFIED: Comprehensive alert scanning with severity levels

=== DATA COLLECTION SCENARIOS ===
These should trigger Data Collection Agent:

1. "Collect latest market data from competitor websites for all laptops"
   Expected: DCA web scraping with visible UI activity
   ✅ VERIFIED: collect_market_data tool with multi-source collection

2. "Gather pricing intelligence from Daraz, Kapruka and other Sri Lankan sites"
   Expected: DCA multi-source data collection with specific sources
   ✅ VERIFIED: Target-specific data collection with progress tracking

3. "Update our market database with fresh competitor pricing data"
   Expected: DCA full refresh workflow with database updates
   ✅ VERIFIED: Comprehensive data refresh with activity logging

=== MULTI-AGENT COORDINATION ===
These should show multiple agents working together:

1. "Collect fresh market data, optimize pricing strategy, and check for critical alerts"
   Expected: DCA -> POA -> ANA coordination workflow
   ✅ VERIFIED: Full multi-agent orchestration with visible handoffs

2. "Update market intelligence and then optimize all laptop prices for maximum profit"
   Expected: DCA -> POA workflow with profit optimization
   ✅ VERIFIED: Sequential agent execution with data flow

3. "Run comprehensive pricing analysis: gather data, optimize with AI, monitor risks"
   Expected: Full multi-agent orchestration (DCA -> POA -> ANA)
   ✅ VERIFIED: Complete workflow with real-time UI feedback

4. "Perform end-to-end pricing optimization using all available agents"
   Expected: Coordinated multi-agent execution with full system demonstration
   ✅ VERIFIED: Maximum complexity demo showing all 4 agents working together

=== DEMONSTRATION FLOW FOR VIVA ===

**RECOMMENDED 6-PHASE DEMO STRATEGY:**

**Phase 1: System Introduction** (30 seconds)
- URL: http://localhost:8501
- Show: "Multi-Agent Dynamic Pricing AI System - 4 Agents Working Together"

**Phase 2: Simple Database Query** (45 seconds)
- Prompt: "What brands do we have available?"
- Show: UIA direct database access, 20 Sri Lankan laptop products

**Phase 3: Agent Handoff Demo** (90 seconds)
- Prompt: "Optimize pricing strategy for gaming laptops using AI algorithms"
- Show: UIA -> POA handoff, Activity tab with real-time agent feedback

**Phase 4: Alert System Demo** (60 seconds)
- Prompt: "Check for any critical pricing situations that need immediate attention"
- Show: UIA -> ANA handoff, alert scanning with severity levels

**Phase 5: Data Collection Demo** (75 seconds)
- Prompt: "Collect latest market data from competitor websites for all laptops"
- Show: UIA -> DCA handoff, multi-source data collection progress

**Phase 6: Multi-Agent Coordination** (120 seconds)
- Prompt: "Collect fresh market data, optimize pricing strategy, and check for critical alerts"
- Show: Full UIA -> DCA -> POA -> ANA workflow with Activity monitoring

**TOTAL DEMO TIME: ~7 minutes**
**BACKUP TIME ALLOWANCE: 3 minutes for questions/issues**

=== UI FEEDBACK EXPECTATIONS ===

**Enhanced Chat UI with Agent Detection:**
- Chat automatically detects agent requirements based on keywords
- Shows staged bubbles before LLM execution:
  * POA: "Analyzing → AI Selection → Market Analysis → Optimization" 
  * DCA: "Planning → Connecting → Ingesting → Updating"
  * ANA: "Loading Rules → Scanning → Evaluating → Compiling"

**Activity View Monitoring:**
- Real-time agent status: "Chat: Processing request..."
- Agent-specific logs: "PriceOptimizer: Starting workflow..."
- Trace ID correlation between chat and activity logs
- Clear completion messages with result summaries

**Keywords That Trigger Agent Bubbles:**
- POA: "optimize price", "pricing strategy", "ai pricing", "algorithm"
- DCA: "collect data", "refresh data", "market data", "scrape"
- ANA: "alerts", "critical", "scan alerts", "anomaly", "breach"

=== TECHNICAL NOTES ===

**Agent Integration Verified:**
- UIA tools mapped correctly:
  * run_pricing_workflow() → POA (complex optimization)
  * collect_market_data() → DCA (data gathering) 
  * scan_for_alerts() → ANA (alert monitoring)

**Agent Classes Confirmed:**
- PricingOptimizerAgent: Full workflow with AI algorithm selection
- DataCollectionAgent: Mock scraping from Sri Lankan sites (daraz.lk, etc.)
- AlertNotificationAgent: Price drop, volatility, and stock alerts

**System Status:**
- Streamlit app runs on port 8501
- Database: 20 Sri Lankan laptop products (LKR 50K-780K)
- Event bus: price.proposal events working
- Timezone handling: Fixed timezone-aware datetime comparisons
"""