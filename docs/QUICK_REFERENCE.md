# Quick Reference Guide

## Event Bus Topics & Payloads

### MARKET_TICK
**Publisher**: DataCollectorAgent  
**Subscribers**: AlertEngine, PricingOptimizerAgent  
**Payload**:
```python
{
    "sku": "SKU-123",
    "market": "DEFAULT",
    "our_price": 99.99,
    "competitor_price": 95.00,
    "timestamp": "2024-01-15T10:30:00Z",
    "source": "web_scraper"
}
```

### PRICE_PROPOSAL
**Publisher**: PricingOptimizerAgent  
**Subscribers**: AutoApplier, GovernanceExecutionAgent, AlertEngine  
**Payload**:
```python
{
    "proposal_id": "uuid",
    "product_id": "SKU-123",
    "previous_price": 99.99,
    "proposed_price": 89.99,
    "algorithm": "rule_based",
    "reasoning": "Competitive undercut",
    "margin": 0.15,
    "timestamp": "2024-01-15T10:35:00Z"
}
```

### PRICE_UPDATE
**Publisher**: AutoApplier, GovernanceExecutionAgent  
**Subscribers**: AlertEngine, analytics services  
**Payload**:
```python
{
    "proposal_id": "uuid",
    "product_id": "SKU-123",
    "final_price": 89.99,
    "applied_by": "AutoApplier",
    "timestamp": "2024-01-15T10:36:00Z"
}
```

### OPTIMIZATION_REQUEST
**Publisher**: Supervisor, manual triggers  
**Subscribers**: PricingOptimizerAgent  
**Payload**:
```python
{
    "request_id": "uuid",
    "sku": "SKU-123",  # Optional, null = all products
    "urgency": "high",  # high, normal, low
    "trigger": "manual"  # manual, scheduled, event_driven
}
```

### MARKET_FETCH_REQUEST
**Publisher**: Any agent needing market data  
**Subscribers**: DataCollectorAgent  
**Payload**:
```python
{
    "request_id": "uuid",
    "sku": "SKU-123",
    "market": "DEFAULT",
    "sources": ["web_scraper", "mock"],
    "urls": ["https://competitor.com/product"],
    "depth": 5
}
```

### MARKET_FETCH_ACK
**Publisher**: DataCollectorAgent  
**Subscribers**: Request originator  
**Payload**:
```python
{
    "request_id": "uuid",
    "job_id": "uuid",
    "status": "RUNNING",  # QUEUED, RUNNING, FAILED
    "error": null  # Error message if FAILED
}
```

### MARKET_FETCH_DONE
**Publisher**: DataCollectorAgent  
**Subscribers**: Request originator  
**Payload**:
```python
{
    "request_id": "uuid",
    "job_id": "uuid",
    "status": "DONE",
    "tick_count": 15
}
```

### ALERT
**Publisher**: AlertEngine, any error-handling agent  
**Subscribers**: Notification services, admin dashboards  
**Payload**:
```python
{
    "alert_id": "uuid",
    "level": "warning",  # info, warning, error, critical
    "title": "Price margin below threshold",
    "message": "Product SKU-123 margin dropped to 8%",
    "timestamp": "2024-01-15T10:40:00Z",
    "metadata": {"sku": "SKU-123", "margin": 0.08}
}
```

---

## MCP Tool Registry

### Data Collector MCP
**Server**: `core/agents/data_collector/mcp_server.py`  
**Tools**:
- `fetch_market_data(sku, market, sources, urls, depth)` → `{"job_id": "uuid"}`
- `get_recent_ticks(sku, limit)` → `[{tick1}, {tick2}, ...]`
- `list_jobs(status)` → `[{job1}, {job2}, ...]`

### Price Optimizer MCP
**Server**: Inferred from `agent.py`  
**Tools**:
- `get_product_info(sku)` → `{"name": "...", "price": 99.99, "cost": 75.00}`
- `get_market_intelligence(sku)` → `{"avg_competitor": 95.00, "trend": "down"}`
- `run_pricing_algorithm(algo, sku, params)` → `{"new_price": 89.99}`
- `validate_price(sku, price)` → `{"valid": true, "warnings": []}`
- `publish_price_proposal(proposal)` → `{"proposal_id": "uuid"}`

---

## SSE Event Examples

### Thinking Event
```
event: thinking
data: {}

```

### Agent Event
```
event: agent
data: {"name": "PriceOptimizer"}

```

### Tool Call Start
```
event: tool_call
data: {"name": "get_product_info", "status": "start"}

```

### Tool Call End
```
event: tool_call
data: {"name": "get_product_info", "status": "end"}

```

### Message Delta
```
event: message
data: {"delta": "Analyzing product pricing..."}

```

### Message Final
```
event: message
data: {
  "id": 123,
  "text": "Recommendation: Reduce price to $89.99",
  "token_in": 250,
  "token_out": 150,
  "cost_usd": 0.0045,
  "model": "gpt-4",
  "provider": "openrouter"
}

```

### Thread Renamed
```
event: thread_renamed
data: {"title": "Pricing Strategy for SKU-123"}

```

### Done Event
```
event: done
data: {}

```

### Error Event
```
event: error
data: {"detail": "LLM provider unavailable"}

```

---

## Database Schema Quick Reference

### pricing_list (app/data.db)
```sql
product_id TEXT PRIMARY KEY
name TEXT
category TEXT
cost REAL
optimized_price REAL  -- Current active price
updated_at TIMESTAMP
```

### decision_log (app/data.db)
```sql
id INTEGER PRIMARY KEY
proposal_id TEXT UNIQUE
sku TEXT
old_price REAL
new_price REAL
margin REAL
algorithm TEXT
decision TEXT  -- AWAITING_MANUAL_APPROVAL, APPLIED_AUTO, etc.
actor TEXT  -- AutoApplier, GovernanceExecutionAgent
created_at TIMESTAMP
```

### market_ticks (app/market.db)
```sql
id INTEGER PRIMARY KEY
sku TEXT
market TEXT
our_price REAL
competitor_price REAL
source TEXT
timestamp TIMESTAMP
```

### settings (app/data.db)
```sql
key TEXT PRIMARY KEY
value TEXT
```
**Common keys**:
- `auto_apply` = "true" | "false"
- `min_margin` = "0.12" (12%)
- `max_delta` = "0.10" (10%)

---

## LLM Provider Failover Chain

```
Request LLM
    ↓
┌─────────────────┐
│  OpenRouter     │ ← Try first
│  (Priority 1)   │
└─────────────────┘
    ↓ (on failure)
┌─────────────────┐
│  OpenAI Direct  │ ← Fallback 1
│  (Priority 2)   │
└─────────────────┘
    ↓ (on failure)
┌─────────────────┐
│  Google Gemini  │ ← Fallback 2
│  (Priority 3)   │
└─────────────────┘
    ↓ (on failure)
Return error + use heuristic fallback
```

**Retry Strategy**: 3 attempts per provider with exponential backoff (0.5s, 1s, 2s)

---

## Testing Checklist

### Before Committing
- [ ] `pytest` passes (all tests)
- [ ] `black .` (Python formatting)
- [ ] `isort .` (Python import sorting)
- [ ] `flake8 .` (Python linting)
- [ ] `npm run lint:fix` (TypeScript linting)
- [ ] `npm run format` (TypeScript formatting)
- [ ] `python scripts/export_openapi.py` (if backend API changed)

### For New Agent
- [ ] Unit test with mocked dependencies
- [ ] Smoke test in `scripts/smoke_<agent>.py`
- [ ] Test with LLM enabled
- [ ] Test with LLM disabled (fallback mode)
- [ ] Verify event publishing to `events.jsonl`
- [ ] Test both MCP and local mode (`USE_MCP=true` and `false`)

### For New API Endpoint
- [ ] Test with mocked `DataRepo`
- [ ] Test auth flow (401 for unauthenticated)
- [ ] Test validation (422 for invalid input)
- [ ] Test success case (200 with correct response)
- [ ] Update `openapi.json`
- [ ] Add frontend React Query hook if needed

### For Streaming Endpoint
- [ ] Emits `thinking` before long operations
- [ ] Emits `agent` on agent switch
- [ ] Emits `tool_call` start/end for each tool
- [ ] Emits `message` deltas during generation
- [ ] Always emits `done` or `error` at end
- [ ] Flushes after each event
- [ ] Frontend watchdog doesn't timeout (< 25s inactivity)

---

## Environment Variables Reference

### Required
```bash
# LLM Providers (at least one)
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
GOOGLE_API_KEY=...

# Database paths (defaults usually work)
APP_DB_PATH=app/data.db
MARKET_DB_PATH=data/market.db
AUTH_DB_PATH=data/auth.db
```

### Optional Feature Flags
```bash
# MCP Mode
USE_MCP=false  # true = distributed, false = local

# Development
DEV_MODE=true  # Enable debug logging

# Authentication
UI_REQUIRE_LOGIN=true  # Force login on frontend

# Agent Behavior
AUTO_APPLY_PRICES=true  # AutoApplier master toggle
MIN_MARGIN=0.12  # Minimum profit margin (12%)
MAX_PRICE_DELTA=0.10  # Max price change (10%)
```

### Testing
```bash
# Disable LLM for deterministic tests
OPENAI_API_KEY=
OPENROUTER_API_KEY=
GOOGLE_API_KEY=

# Use local mode for unit tests
USE_MCP=false
```

---

## Common Command Sequences

### Full Development Setup
```bash
# Backend setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install

# Database initialization
python scripts/init_db.py
python scripts/create_sample_catalog.py
python scripts/insert_mock_market_data.py

# Run application
run_full_app.bat
```

### Run All Tests
```bash
# Python tests
pytest -v

# TypeScript tests
cd frontend
npm run test

# E2E tests (requires app running)
cd frontend
npm run test:e2e
```

### Debug Event Flow
```bash
# Watch events in real-time
Get-Content data\events.jsonl -Wait -Tail 10 | ConvertFrom-Json

# Or filter specific topic
Get-Content data\events.jsonl -Wait | Select-String "PRICE_PROPOSAL"
```

### Manual Agent Execution
```bash
# Run pricing for specific product
python scripts/run_pricing_agent_once.py --sku SKU-123

# Collect market data
python scripts/run_autonomous_data_collector.py

# Apply pending proposals
python scripts/run_auto_applier.py
```

---

## File Location Reference

### Agent Implementations
- `core/agents/supervisor.py` - Workflow orchestrator
- `core/agents/price_optimizer/agent.py` - LLM-powered pricing
- `core/agents/auto_applier.py` - Autonomous price application
- `core/agents/governance_execution_agent.py` - Enhanced governance
- `core/agents/data_collector/collector.py` - Market data ingestion
- `core/agents/alert_engine/agent.py` - Alert generation

### Infrastructure
- `core/agents/agent_sdk/bus_factory.py` - Event bus singleton
- `core/agents/agent_sdk/protocol.py` - Event topic definitions
- `core/agents/llm_client.py` - Multi-provider LLM client
- `core/agents/chat_executor.py` - Tool execution engine
- `core/agents/agent_sdk/mcp_client.py` - MCP connection pooling

### Frontend State
- `frontend/src/store/messageStore.ts` - Chat messages + streaming
- `frontend/src/store/threadStore.ts` - Thread list management
- `frontend/src/lib/api/sseClient.ts` - SSE parsing + watchdog

### Backend API
- `backend/routers/messages.py` - Chat endpoints + SSE streaming
- `backend/routers/catalog.py` - Product management
- `backend/routers/prices.py` - Pricing list operations
- `backend/main.py` - FastAPI app entry point

### Database & Config
- `data/events.jsonl` - Event journal (append-only)
- `app/data.db` - Application database (pricing, decisions, settings)
- `data/market.db` - Market data (ticks, intelligence)
- `data/auth.db` - Authentication (users, sessions)
- `.env` - Environment configuration
