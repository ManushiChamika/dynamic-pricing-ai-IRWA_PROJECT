# Viva Preparation - Agent Communication & Protocol Deep Dive

## Part 1: Technical Depth Questions (5 marks)

### Q1: "Explain your agent architecture and why you chose this approach"

**Strong Answer:**
```
FluxPricer uses a 4-agent microservice architecture:

1. DATA COLLECTOR: Ingests market data from APIs, normalizes, catalogs
2. PRICE OPTIMIZER: Analyzes data, runs algorithms, generates proposals
3. ALERT SERVICE: Validates fairness, monitors thresholds, gates changes
4. USER INTERACTION: Parses NLP, orchestrates multi-agent workflows

We chose this because:
- Single Responsibility: Each agent does ONE job well
- Scalability: Add "Fraud Detection Agent" without touching others
- Auditability: Every interaction logged (compliance)
- Resilience: One agent failure doesn't cascade

The key insight: Pricing is a GOVERNANCE problem, not just computation.
Alert Service acts as a governance layer—no unethical prices escape.
```

### Q2: "How do agents communicate? Walk us through a message"

**Strong Answer:**
```
Two communication layers:

LAYER 1: MCP (Synchronous Tool Calls)
- Price Optimizer needs market data
- Sends: tools/call message to Data Collector
  {
    "type": "tools/call",
    "call_id": "call_123",
    "source_agent": "price_optimizer_001",
    "target_agent": "data_collector_001",
    "tool_name": "get_market_data",
    "tool_input": {"product_id": "asus_rog_g16_01", "days_back": 30}
  }
- Data Collector executes, responds: tools/result
  {
    "type": "tools/result",
    "call_id": "call_123",
    "status": "success",
    "result": {"records": 42, "avg_price": 1189},
    "execution_time_ms": 23
  }

LAYER 2: Event Bus (Asynchronous Pub-Sub)
- Data Collector publishes: event/notify
  {
    "type": "event/notify",
    "event_type": "market_data_updated",
    "source_agent": "data_collector_001",
    "event_data": {"product_id": "asus_rog_g16_01", "records": 42}
  }
- ALL subscribers notified simultaneously:
  - Price Optimizer starts analysis
  - Alert Service stands by
  - User Interaction shows progress
- Event persisted to events.jsonl (audit trail)

Why both layers?
- MCP: When you need guaranteed response (Price Optimizer needs data)
- Event Bus: When you want loose coupling (Alert Service doesn't block anything)
```

### Q3: "What's your event journal? Why is it important?"

**Strong Answer:**
```
events.jsonl is an immutable append-only log in data/events.jsonl

Every interaction is recorded:
{
  "ts": "2025-10-18T15:30:00.000Z",
  "topic": "market.tick",
  "payload": {"sku": "asus_rog_g16_01", "price": 1189}
}
{
  "ts": "2025-10-18T15:30:15.000Z",
  "topic": "price.proposal",
  "payload": {"sku": "asus_rog_g16_01", "proposed_price": 1249, "confidence": 0.94}
}
{
  "ts": "2025-10-18T15:30:30.000Z",
  "topic": "alert.event",
  "payload": {"sku": "asus_rog_g16_01", "kind": "FAIRNESS_CHECK", "passed": true}
}

Why important:
1. COMPLIANCE: Audit trail for regulatory requirements
2. DEBUG: Replay events to understand what happened
3. TRUST: Customers see decisions were fair and transparent
4. MONITORING: Identify patterns, anomalies in pricing
5. RESPONSIBLE AI: Prove fairness checks were performed

This is industry standard—similar to how banks audit transactions.
```

### Q4: "Why MCP instead of REST APIs or database triggers?"

**Strong Answer:**
```
Evaluation Matrix:

┌─────────────────┬──────────────┬──────────────┬──────────────┐
│ Approach        │ Latency      │ Coupling     │ Auditability │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ REST APIs       │ 100-200ms    │ Tight        │ Poor         │
│ DB Triggers     │ 50-100ms     │ Very Tight   │ Poor         │
│ Message Queue   │ 10-50ms      │ Loose        │ Good         │
│ MCP (chosen)    │ 1-50ms       │ Loose        │ Excellent    │
└─────────────────┴──────────────┴──────────────┴──────────────┘

MCP advantages:
1. INDUSTRY STANDARD: Protocol from Anthropic (makers of Claude)
2. SELF-DOCUMENTING: Tools describe themselves with schemas
3. EXTENSIBLE: Add new tools without core changes
4. AUDITABLE: All messages logged automatically
5. LLM-NATIVE: Built for AI agents (like Claude's plugin system)

REST APIs would require:
- Manual logging
- N² connections (every agent talks to every other)
- High latency for coordination
- Not designed for LLM agents

Database triggers would create:
- Tight coupling (agents must share schema)
- Race conditions (concurrent updates)
- No message history
- Hard to debug

MCP provides best of both worlds: speed + clarity + auditability.
```

### Q5: "How does your system handle agent failures?"

**Strong Answer:**
```
Multi-layered resilience:

1. BUS RESILIENCE (Event Bus)
   - If one subscriber crashes, others continue
   - Error caught: "bus_sink_error" logged
   - Affected subscriber must be restarted, but system keeps running
   
   Code example (bus_factory.py):
   ```python
   for cb in list(self._subs.get(topic, [])):
       try:
           res = cb(message)
           if asyncio.iscoroutine(res):
               await res
       except Exception as e:
           log.warning("bus_sink_error", error=str(e))
           # Continue to next subscriber ← Key resilience point
   ```

2. TOOL CALL TIMEOUT
   - MCP calls have timeout
   - If Data Collector hangs, Price Optimizer gets error response
   - Optimizer can retry or use cached data
   
3. SCHEMA VALIDATION
   - Invalid messages rejected before processing
   - Prevents downstream agents from crashing
   
4. SUPERVISOR ORCHESTRATION
   - For critical workflows, Supervisor re-runs failed stages
   - Ensures catalog import → data collection → pricing completes
   
5. EVENT JOURNAL RECOVERY
   - If system crashes, replay events.jsonl
   - Resume from last good state
   - No work lost

In production, you'd add:
- Circuit breaker pattern (skip failed agent temporarily)
- Health checks (probe agents periodically)
- Dead letter queue (log failed messages for manual review)
```

### Q6: "How does your system enforce Responsible AI?"

**Strong Answer:**
```
The Alert Service Agent is our governance layer:

FAIRNESS VALIDATION:
```python
def validate_fairness(product_id, recommended_price):
    # Check price variance doesn't exceed threshold
    market_avg = get_market_average(product_id)
    variance = abs(recommended_price - market_avg) / market_avg
    
    if variance > 0.05:  # 5% threshold
        return {"is_fair": False, "reason": "Price too far from market"}
    return {"is_fair": True}
```

MARGIN PROTECTION:
```python
def check_margin_sufficient(cost, proposed_price):
    margin = (proposed_price - cost) / proposed_price
    
    if margin < 0.10:  # 10% minimum
        return {"valid": False, "reason": "Margin below sustainable level"}
    return {"valid": True}
```

UNDERCUT DETECTION:
```python
def detect_undercut(product_id, our_price, competitor_prices):
    min_competitor = min(competitor_prices)
    undercut_threshold = min_competitor * 1.01  # Allow 1% below
    
    if our_price < undercut_threshold:
        return {"undercut": True, "gap": undercut_threshold - our_price}
    return {"undercut": False}
```

GOVERNANCE FLOW:
1. Price Optimizer generates recommendation
2. Recommendation published: price.proposal event
3. Alert Service subscribes to this event
4. ALL checks run: fairness → margin → undercut
5. Only if ALL pass, publish: recommendation_validated
6. User Interaction only shows validated recommendations

KEY POINT: Price Optimizer CANNOT bypass Alert Service.
It's architecturally enforced—not a suggestion.

This is Responsible AI because:
✅ Fairness: Objective metrics, not subjective
✅ Transparency: Every check logged
✅ Auditability: Full decision trail
✅ Explainability: Reasons documented
✅ Human-in-the-loop: Humans can override with warnings
```

---

## Part 2: Communication Protocol Understanding (4 marks)

### Key Concepts to Master

**Synchronous vs Asynchronous:**
```
SYNCHRONOUS (MCP):
  Request → Wait → Response
  Example: "Get market data for asus_rog_g16_01"
  Latency: ~23ms (from logs)
  Guarantees: Response received (or error returned)
  
ASYNCHRONOUS (Event Bus):
  Publish → Fire-and-forget
  Example: "Market data updated, everyone listen"
  Latency: ~8ms (journal write) + subscriber processing
  Guarantees: Published to all subscribers who are listening
```

**Pub-Sub Topics (memorize these):**
```
market.tick          → New price data arrived
market.fetch.*       → Data collection lifecycle events
price.proposal       → New pricing recommendation
alert.event          → Alert triggered
price.update         → Price changed in system
chat.*               → User interaction events
```

**Message Schema Components:**
```
All MCP messages have:
- type: "tools/call" | "tools/result" | "error" | "event/notify"
- call_id or event_id: UUID for tracking
- source_agent: Which agent sent it
- target_agent: Which agent should receive it (for calls)
- timestamp: ISO 8601 UTC
- payload: Custom data

Example call_id: "call_001_market_data"
- Prefix: "call_" or "evt_" (distinguishes type)
- Sequence: "001" (order in workflow)
- Description: "market_data" (human-readable)
```

---

## Part 3: Individual Contribution Angle (5 marks)

### How to Discuss Your Role

**For Data/Backend Engineer:**
```
"I implemented the Data Collector Agent and Event Bus infrastructure.

Specifically:
1. DataCollectorAgent orchestrates market data collection
   - Handles API pagination
   - Normalizes pricing formats
   - Publishes market_data_updated events

2. Event Bus (_AsyncBus in bus_factory.py)
   - Manages Pub-Sub subscriptions
   - Dispatches events to all subscribers
   - Handles async/sync callbacks uniformly

3. Journal System (events/journal.py)
   - Persists all events to events.jsonl
   - Atomic writes (never partial)
   - Recovery mechanism if system crashes

Key challenge: Making event bus resilient to subscriber failures
while maintaining message order guarantees."
```

**For ML/Pricing Engineer:**
```
"I implemented the Price Optimizer Agent and pricing algorithms.

Specifically:
1. PricingOptimizerAgent coordinates optimization workflow
   - Calls Data Collector for market data
   - Runs algorithm selection (rule-based vs ML)
   - Publishes recommendations as events

2. Pricing Algorithms
   - rule_based: Conservative competitive pricing
   - ml_model: Advanced trend analysis + volatility
   
3. Tool Integration
   - get_market_data: Fetches competitor pricing
   - get_competitor_prices: Analyzes competitors
   - analyze_demand: Trend detection

Key challenge: Ensuring recommendations pass fairness validation
before being shown to users."
```

**For Frontend/UX Engineer:**
```
"I implemented the User Interaction Agent and chat interface.

Specifically:
1. UserInteractionAgent processes user messages
   - NLP parsing (intent + entities)
   - Context management (conversation history)
   - Multi-turn dialogue support

2. Chat API Integration
   - Translates user messages to agent calls
   - Streams responses (SSE for real-time)
   - Handles tool execution orchestration

3. Visualization of Agent Workflows
   - Show which agent is processing
   - Display audit trail (events.jsonl)
   - Timeline of recommendation generation

Key challenge: Making complex agent coordination feel simple to users.
One query triggers 4 agents—but user sees one coherent response."
```

---

## Part 4: Commercialization Connection (3 marks)

### Tie Communication Architecture to Business Value

**Q: "How does your agent architecture differentiate your product?"**

**Answer:**
```
SPEED:
- Synchronous MCP + Event Bus = ~1.5 seconds end-to-end
- Competitors using REST APIs: 3-5 seconds
- Customers get pricing recommendations FAST
→ Business value: Higher conversion rate

TRUST:
- Complete audit trail (events.jsonl)
- Fairness checks automated and logged
- Regulatory compliance built-in
→ Business value: Enterprise customers, regulated markets

SCALABILITY:
- Add new agents without touching existing code
- Example: "Fraud Detection Agent" plugs in via event bus
- Deploy to customers in days, not weeks
→ Business value: Faster feature delivery, longer sales cycle

RELIABILITY:
- Event Bus resilience prevents cascading failures
- One agent crash ≠ entire system down
- Customer confidence in system stability
→ Business value: SLA compliance, lower churn
```

---

## Part 5: Demo Points for Viva

### What to Show/Demonstrate

**1. System Diagram**
```
Pull up: docs/system_architecture.mmd
Show: 4 agents, event bus, database connections
Explain: Information flow, color coding (agents/storage/sinks)
```

**2. Event Journal**
```
Pull up: data/events.jsonl
Show: Live events being written
Explain: "Each line is a complete audit trail entry"
Filter: grep "price.proposal" events.jsonl
Show: "All recommendations are here, with timestamps"
```

**3. MCP Protocol Example**
```
Pull up: docs/MCP_PROTOCOL.md (lines 173-217)
Show: Actual JSON message formats
Explain: "This is how agents talk—standardized, not ad-hoc"
```

**4. Supervisor Workflow**
```
Pull up: core/agents/supervisor.py (lines 39-156)
Show: How supervisor orchestrates workflow
Run script: python scripts/smoke_price_optimizer.py
Show: Console output showing each agent executing
```

**5. Alert Service Fairness**
```
Pull up: core/agents/alert_notifier.py (lines 14-47)
Show: Fairness thresholds
Explain: "This prevents unethical pricing—architectural enforcement"
```

---

## Part 6: Anticipated Difficult Questions

### Q: "Isn't this over-engineered for a startup?"

**Answer:**
```
Good question. But consider:

1. START SMALL, SCALE UP: Single-agent prototype → 4-agent system
2. EARLY INVESTMENT: MCP/Event Bus now = easier to add features later
3. REGULATORY: Even startups need auditability (SLA requirements)
4. CUSTOMER TRUST: "Here's your complete audit trail" = selling point

Most startups regret NOT building for scale early. We did it right.
```

### Q: "What if an agent is slow—does it block others?"

**Answer:**
```
No, because of asynchronous pub-sub:

Event Bus:
- Data Collector publishes market_data_updated
- Alert Service receives immediately
- Price Optimizer might be slow, still gets message
- Each subscriber independent

MCP:
- Price Optimizer calls Data Collector for data
- Only Price Optimizer waits (with timeout)
- Other agents unaffected

Timeouts prevent hard blocking:
```python
result = await dc_client.get_market_data(sku, timeout_s=5)
# If slower than 5s, returns error, continues
```
```

### Q: "How do you test agent communication?"

**Answer:**
```
Three testing levels:

1. UNIT TESTS: Test each agent independently
   - Mock event bus
   - Mock other agents
   - Verify tool execution
   
2. INTEGRATION TESTS: Test agent interactions
   - Real event bus
   - Verify message flow
   - Check audit trail writes
   
3. END-TO-END: Full workflow test
   - scripts/smoke_end_to_end.py
   - Real data, real algorithms
   - Verify complete flow works

We log all events, so testing is:
1. Run workflow
2. Check events.jsonl for expected sequence
3. Assert compliance (fairness checks passed)
```

---

## Part 7: Final Tips

### Be Specific, Not Generic

❌ BAD: "We use agents to coordinate pricing"
✅ GOOD: "Data Collector publishes market_data_updated events to Event Bus. Price Optimizer subscribes, runs ml_model algorithm, and publishes recommendation_generated. Alert Service validates fairness thresholds before User Interaction shows result. All logged to events.jsonl."

### Reference Code

❌ BAD: "We have an event bus"
✅ GOOD: "The event bus is in core/agents/agent_sdk/bus_factory.py. The publish method writes to events.jsonl at line 41, dispatches to subscribers at line 46. It's resilient—if one subscriber fails, others still get notified (line 51-57)."

### Show Tradeoffs

❌ BAD: "MCP is the best"
✅ GOOD: "We evaluated MCP vs REST vs shared database. REST was too chatty (100-200ms latency vs 10-50ms). Shared database created race conditions. MCP provided standardized communication with full auditability—critical for a pricing system where fairness matters."

### Connect to Business

❌ BAD: "We use an asynchronous event bus"
✅ GOOD: "The asynchronous event bus lets us add new agents without modifying existing code. Want fraud detection? New agent subscribes to price.proposal events. Deploy in a day, not a week. That's competitive advantage."

---

**You're now prepared for deep technical questions on communication protocols. The key is showing you understand not just WHAT you built, but WHY and HOW to defend it.**
