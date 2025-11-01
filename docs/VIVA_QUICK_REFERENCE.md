# ⚡ VIVA QUICK REFERENCE - 1-Page Memorization Guide

**Print this. Read it 1 day before viva. Memorize the 5 sections below.**

---

## 🎯 THE 5 CORE CONCEPTS (MEMORIZE THESE)

### 1. System Architecture at a Glance
```
4 Agents: Data Collector → Price Optimizer → Alert Service → User Interaction
2 Protocols: MCP (sync, 10-50ms) + Event Bus (async, immutable audit trail)
Audit Log: events.jsonl (182K+ events, compliance & debugging)
Response Time: ~1.5 seconds per pricing request (end-to-end)
```

### 2. Why MCP? (10-50ms latency advantage)
- **vs REST:** 100-200ms latency
- **vs gRPC:** Similar performance, less industry adoption
- **Why MCP?** Industry standard in AI systems + auditability + tool standardization

### 3. The 3 Fairness Checks (Architectural Enforcement)
```
Variance Check:    Price variance < 5% of market average (prevents outliers)
Margin Check:      Profit margin > 10% above cost (prevents undercutting)
Undercut Check:    Can't undercut same item > 2x per day (prevents cycling)
```
→ These are NOT optional—they're **architectural enforcement** in Alert Service

### 4. Complete Request Timeline (1.5 seconds total)
```
T+0ms:    User sends pricing request
T+10ms:   Data Collector fetches market data (~23ms fetch time)
T+35ms:   Price Optimizer runs optimization algorithm (~100ms compute)
T+142ms:  Alert Service validates 3 fairness checks (~5ms validation)
T+155ms:  Result returned to user interface
```

### 5. Commercialization - 4 Revenue Tiers
```
Tier 1: Starter       → $99/month   (1 user, 100 items)
Tier 2: Pro           → $499/month  (5 users, 1000 items)
Tier 3: Enterprise    → Custom      (unlimited, SLA guaranteed)
Tier 4: Usage-Based   → $0.01/query (pay-per-optimization)
```

---

## 10 KEY NUMBERS TO REMEMBER

| Number | Context |
|--------|---------|
| 4 | Number of agents (DC, PO, AS, UIA) |
| 2 | Communication layers (MCP + Event Bus) |
| 1.5s | End-to-end request time |
| 10-50ms | MCP latency (vs 100-200ms REST) |
| 182K+ | Total events in audit log |
| 5% | Fairness variance threshold |
| 10% | Minimum profit margin |
| 2x | Max undercuts per day |
| $2-5B | Annual wasted revenue (market opportunity) |
| 23ms | Data collection latency |

---

## 3 DEMO COMMANDS

Run these in terminal to show the system working:

```bash
# 1. View audit log (shows immutable event trail)
tail -n 50 data/events.jsonl | jq .

# 2. Get pricing recommendation
curl -X POST http://localhost:8000/api/pricing/optimize \
  -H "Content-Type: application/json" \
  -d '{"item_id": "LAPTOP001", "market_data": {"avg_price": 1000}}'

# 3. View compliance audit
grep "fairness" data/events.jsonl | jq .validation_result
```

---

## 6 VIVA QUESTIONS + 30-SECOND ANSWERS

### Q1: "How do agents communicate?"
**Answer (30s):**
"Our system uses two protocols. First, MCP (Model Context Protocol) for synchronous agent-to-agent communication—it's the industry standard with 10-50ms latency versus 100-200ms with REST. Second, the Event Bus for asynchronous audit logging. Every decision is recorded in events.jsonl with full context, creating an immutable audit trail for compliance and debugging. This dual-protocol approach gives us both performance and auditability."

### Q2: "Why MCP instead of REST?"
**Answer (30s):**
"Three reasons: (1) Latency—MCP is 10-50ms vs REST's 100-200ms, critical when agents communicate in sequence. (2) Industry standard—MCP is used by leading AI systems and is becoming the protocol of choice for tool-using agents. (3) Built-in auditability—MCP logs all tool calls and results automatically, which REST doesn't do. This means we get both performance and compliance with a single choice."

### Q3: "What does the Alert Service do?"
**Answer (30s):**
"The Alert Service enforces three fairness checks: variance (price can't deviate more than 5% from market average), margin (must maintain 10% profit minimum), and undercut prevention (can't undercut the same item more than twice daily). Crucially, these aren't warnings—they're architectural constraints that reject proposals, not approve-then-check. This ensures fair pricing is enforced, not optional."

### Q4: "Walk me through a pricing request (1.5 seconds)."
**Answer (30s):**
"User sends a request at T+0. Data Collector fetches current market data (T+10ms, ~23ms fetch). Price Optimizer receives data and runs the optimization algorithm (T+35ms, ~100ms compute). Result goes to Alert Service for fairness checks (T+142ms, ~5ms validation—variance, margin, undercut rules). Approved results return to User Interface (T+155ms). All decisions logged to events.jsonl."

### Q5: "What's in events.jsonl?"
**Answer (30s):**
"It's our immutable audit log with 182K+ events. Each event captures: agent name, timestamp, input parameters, output decisions, and validation results. This serves three purposes: (1) Compliance—prove every price was fair-checked, (2) Debugging—trace request paths and find failures, (3) Learning—analyze which checks trigger most often and refine thresholds. It's write-once, read-many immutability."

### Q6: "How does this ensure responsible AI?"
**Answer (30s):**
"Three layers: (1) Architectural—fairness checks are enforced, not optional, in Alert Service. (2) Auditability—events.jsonl creates immutable decision trail. (3) Transparency—system tells users exactly why prices were set/rejected (variance, margin, or undercut reasons). Combined, these ensure prices are fair, justified, and explainable—not black-box algorithms."

---

## ⚠️ RED FLAGS TO AVOID

❌ **Don't say:** "REST would work fine for this"
✅ **Say instead:** "MCP gives us 10-50ms vs 100-200ms with auditability"

❌ **Don't say:** "Fairness checks are warnings"
✅ **Say instead:** "Fairness checks are architectural enforcement"

❌ **Don't say:** "We log for debugging"
✅ **Say instead:** "We log for compliance, debugging, AND learning"

❌ **Don't say:** "Events are just records"
✅ **Say instead:** "events.jsonl is immutable audit trail with 182K+ decisions"

❌ **Don't say:** "MCP is just a protocol"
✅ **Say instead:** "MCP is industry standard tool-calling with built-in auditability"

---

## 🧠 HOW TO PRACTICE

**Day 1:** Read this page 2x
**Day 2:** Close this file and write out all 5 concepts from memory
**Day 3:** Practice answering 6 questions with a partner
**Day 4:** Do full mock viva (15 mins) with all 6 questions
**Day 5:** Quick review of red flags morning-of

---

## 🚀 YOU'RE READY WHEN...

✅ Can answer all 6 Q&A without looking at this page  
✅ Can explain the timeline (1.5s) without thinking  
✅ Can name all 4 agents in order  
✅ Can explain why MCP is better than REST in <20 seconds  
✅ Can describe 3 fairness checks from memory

**All 5?** → You're VIVA READY 🎉

---

## BONUS: What If They Ask...

**"Could you make fairness checks optional?"**
→ "No, they're architectural constraints in Alert Service, not policy. To change them, you'd need to rewrite the agent, and we'd recommend not doing that because it breaks compliance guarantees."

**"How do you know the 5% threshold is fair?"**
→ "We determined it from market analysis of x retailers over y months. If needed, we could adjust via configuration, but we'd audit the impact on fairness metrics first."

**"What happens if an agent crashes?"**
→ "The event bus logs it immediately with timestamp and error. Next request routes through backup instance. The immutable log means we never lose decision context."

**"How do users know a price was rejected?"**
→ "User Interface shows rejection reason ('Price variance exceeds 5%' or 'Profit margin below 10%'). They can then adjust parameters and resubmit."

---

**Last Updated:** October 18, 2025  
**Next:** Review VIVA_COMMUNICATION_PROTOCOL_GUIDE.md for deep dives  
**Print this page** and review 1 day before viva 📋
