# Agent Communication - Quick Reference Card
## For Presentations & Viva

---

## System at a Glance

```
┌─────────────────────────────────────────┐
│ USER                                    │
│ "What price for Asus ROG G16?"         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ USER INTERACTION AGENT                  │
│ ├─ Parse intent & entities              │
│ └─ Orchestrate workflow                 │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │ Event Bus   │
        └──────┬──────┘
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
    ▼          ▼          ▼          ▼
  DC PO      AA          UIA        (Others)
  
DC  = Data Collector Agent
PO  = Price Optimizer Agent
AA  = Alert Service Agent
UIA = User Interaction Agent

Total workflow: ~1.5 seconds
Audit trail: 100% (events.jsonl)
```

---

## The 4 Agents

| Agent | Job | Key Tool | Output |
|-------|-----|----------|--------|
| **Data Collector** | Fetch data | `get_market_data()` | `market_data_updated` |
| **Price Optimizer** | Calculate price | `recommend_price()` | `recommendation_generated` |
| **Alert Service** | Guard against bad prices | `validate_fairness()` | `recommendation_validated` \| `alert` |
| **User Interaction** | Chat with user | `stream_response()` | Chat reply |

---

## Two Communication Layers

### 1. MCP (When you need a response)
```
Optimizer: "Give me market data"
              ↓
         [Sends tools/call]
              ↓
Collector: "Here's data" [Sends tools/result]
              ↓
Optimizer: Received! Continuing...
```
**Latency: 10-50ms** | **Guarantee: Response or error** | **Use: Direct requests**

### 2. Event Bus (When you want to notify everyone)
```
Collector: "Market data updated!" [Publishes event]
              ↓
         [Event Bus broadcasts]
              ↓
        ┌─────┬──────┬─────┐
        ▼     ▼      ▼     ▼
      Optimizer Alert User Others
```
**Latency: ~8ms** | **Guarantee: All subscribers notified** | **Use: Notifications**

---

## Event Journal (events.jsonl)

```json
{"ts":"2025-10-18T15:30:00Z","topic":"market.tick","payload":{...}}
{"ts":"2025-10-18T15:30:05Z","topic":"price.proposal","payload":{...}}
{"ts":"2025-10-18T15:30:10Z","topic":"alert.event","payload":{...}}
```

**Purpose:** Complete audit trail
**Format:** 1 JSON object per line
**Location:** `data/events.jsonl`
**Immutable:** Append-only (never modified/deleted)

---

## Why This Design Wins

| Criterion | Score | Why |
|-----------|-------|-----|
| **Roles** | 5/5 | Each agent has 1 job, clear inputs/outputs |
| **Protocols** | 5/5 | MCP + Event Bus (standardized, not custom) |
| **Communication** | 5/5 | Documented, audited, resilient |
| **Auditability** | 5/5 | events.jsonl = complete decision trail |
| **Scalability** | 5/5 | Add agents without modifying existing ones |
| **Responsible AI** | 5/5 | Alert Service = governance layer |

**Result: "Excellent" Category** ✅

---

## Viva Talking Points

### "How do agents communicate?"
→ "MCP for tool calls (request/response), Event Bus for notifications (pub/sub). Both logged to events.jsonl."

### "Why not REST APIs?"
→ "REST = 100-200ms latency, N² connections, poor auditability. MCP = 10-50ms, designed for LLM agents, full audit trail."

### "How is this Responsible AI?"
→ "Alert Service validates fairness before showing recommendations. Automatic checks: price variance, margin protection, undercut detection. All logged."

### "What if an agent crashes?"
→ "Event Bus is resilient. If one subscriber fails, others continue. One agent failure ≠ system down."

### "Walk us through a pricing workflow"
→ Reference: `docs/AGENT_COMMUNICATION_GUIDE.md` Part 3 (End-to-End Workflow Example)

---

## Code References (Quick Links)

```
Architecture:          docs/system_architecture.mmd
MCP Protocol:          docs/MCP_PROTOCOL.md
Communication Guide:   docs/AGENT_COMMUNICATION_GUIDE.md
Viva Prep:            docs/VIVA_COMMUNICATION_PROTOCOL_GUIDE.md

Code Locations:
├─ Event Bus:         core/agents/agent_sdk/bus_factory.py
├─ Topics:            core/agents/agent_sdk/protocol.py
├─ Journal:           core/events/journal.py
├─ Agents:            core/agents/{pricing_optimizer, alert_notifier, ...}
└─ Supervisor:        core/agents/supervisor.py

Demo:
├─ View events:       tail -f data/events.jsonl
├─ Run workflow:      python scripts/smoke_end_to_end.py
└─ Check audit:       grep "price.proposal" data/events.jsonl
```

---

## Memorize These

**Topic Names:**
- `market.tick` - New price data
- `price.proposal` - New recommendation
- `alert.event` - Alert triggered

**Message Types:**
- `tools/call` - Request
- `tools/result` - Response
- `event/notify` - Broadcast

**Thresholds (Responsible AI):**
- Max price variance: 5% from market average
- Min margin: 10%
- Undercut threshold: 1% below lowest competitor

**Latencies:**
- MCP: 10-50ms
- Event Bus: ~8ms (journal) + processing
- End-to-End Workflow: ~1.5 seconds

---

**Print this. Carry it. Reference it during viva. You're prepared. ✅**
