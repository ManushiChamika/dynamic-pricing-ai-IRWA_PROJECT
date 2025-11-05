# Developer Onboarding Guide

Welcome to the Dynamic Pricing AI system! This guide will help you understand the architecture and start contributing quickly.

## Table of Contents
1. [System Overview](#system-overview)
2. [Getting Started](#getting-started)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [Development Workflow](#development-workflow)
5. [Common Tasks](#common-tasks)
6. [Debugging Guide](#debugging-guide)
7. [Best Practices](#best-practices)

---

## System Overview

### What Does This System Do?

This is an **AI-powered dynamic pricing platform** that:
- **Monitors** competitor prices in real-time
- **Analyzes** market conditions using LLM-powered agents
- **Proposes** optimal pricing strategies
- **Automatically applies** price changes (with guardrails)
- **Alerts** stakeholders about critical events

### Key Innovations

1. **Event-Driven Agent Architecture**: Loosely-coupled autonomous agents communicate via pub-sub event bus
2. **LLM Orchestration**: Multi-step reasoning with automatic tool selection and execution
3. **Dual-Mode Operation**: Same codebase runs locally (dev) or distributed (prod) via MCP toggle
4. **Real-Time Streaming**: Live updates to frontend via Server-Sent Events
5. **Autonomous Governance**: Business rules enforced automatically with full audit trail

### Technology Stack

**Frontend**: React + TypeScript + Vite + Tailwind CSS + Zustand + TanStack Query  
**Backend**: Python + FastAPI + SQLAlchemy + Pydantic  
**AI**: OpenAI/OpenRouter/Gemini (multi-provider failover)  
**Infrastructure**: Event Bus (pub-sub) + MCP (Model Context Protocol) + SQLite/PostgreSQL

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Git**
- **API Key** for at least one LLM provider (OpenAI, OpenRouter, or Google Gemini)

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd dynamic-pricing-ai-IRWA_PROJECT
   ```

2. **Backend setup**:
   ```bash
   # Create virtual environment
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Frontend setup**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure environment**:
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env and add your API keys
   # Minimum required: One of OPENAI_API_KEY, OPENROUTER_API_KEY, or GOOGLE_API_KEY
   ```

5. **Initialize databases**:
   ```bash
   python scripts/init_db.py
   python scripts/create_sample_catalog.py
   python scripts/insert_mock_market_data.py
   ```

6. **Run the application**:
   ```bash
   run_full_app.bat  # Windows
   # Or manually:
   # Terminal 1: uvicorn backend.main:app --reload --port 8000
   # Terminal 2: cd frontend && npm run dev
   ```

7. **Open in browser**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

8. **Login with test credentials**:
   - Email: `demo@example.com`
   - Password: `1234567890`

---

## Architecture Deep Dive

### Directory Structure

```
dynamic-pricing-ai-IRWA_PROJECT/
├── backend/              # FastAPI REST API
│   ├── routers/          # API endpoint definitions
│   └── tests/            # Backend unit tests
├── core/                 # Business logic & agents
│   ├── agents/           # Autonomous agent implementations
│   │   ├── agent_sdk/    # Shared agent infrastructure
│   │   ├── price_optimizer/  # LLM-powered pricing agent
│   │   ├── data_collector/   # Market data ingestion
│   │   └── alert_engine/     # Alert generation
│   └── events/           # Event schemas & validation
├── frontend/             # React single-page application
│   └── src/
│       ├── components/   # React components
│       ├── store/        # Zustand state management
│       ├── hooks/        # Custom React hooks
│       └── lib/          # Utilities & API client
├── scripts/              # Automation & maintenance
│   ├── debug/            # Debugging utilities
│   └── smoke_*.py        # Integration smoke tests
├── data/                 # SQLite databases & event logs
│   └── events.jsonl      # Event journal (audit trail)
└── docs/                 # Documentation
```

### Core Concepts

#### 1. Event-Driven Architecture

**All agents communicate via an event bus**. This enables:
- **Loose coupling**: Agents don't need to know about each other
- **Scalability**: Add new agents without modifying existing ones
- **Observability**: Every event is logged to `data/events.jsonl`
- **Asynchrony**: Agents react to events independently

**Example**: Data collector publishes `MARKET_TICK` → Pricing optimizer subscribes and reacts

```python
# Publishing an event
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic

await get_bus().publish(Topic.MARKET_TICK.value, {
    "sku": "SKU-123",
    "competitor_price": 95.00,
    "timestamp": "2024-01-15T10:30:00Z"
})

# Subscribing to events
async def on_market_tick(tick):
    print(f"Received tick: {tick}")

get_bus().subscribe(Topic.MARKET_TICK.value, on_market_tick)
```

#### 2. LLM Tool Orchestration

**Agents use LLMs to make autonomous decisions**. The workflow:

1. Agent defines a **system prompt** describing its workflow
2. Agent registers **tools** (functions) the LLM can call
3. LLM **analyzes** the situation
4. LLM **selects and calls** appropriate tools
5. LLM **synthesizes** results into final decision

**Example**: Pricing optimizer uses LLM to select algorithm based on market conditions

```python
# Agent provides tools
tools = [
    get_product_info,
    get_market_intelligence,
    run_pricing_algorithm,
    validate_price,
    publish_price_proposal
]

# LLM orchestrates multi-step workflow
response = await llm_client.chat_with_tools(
    messages=[{"role": "system", "content": system_prompt}],
    tools=tools,
    max_rounds=5  # Allow up to 5 tool-call iterations
)
```

**Fallback**: Every LLM-powered agent has **deterministic heuristics** for when LLM is unavailable.

#### 3. MCP Dual-Mode Operation

**MCP (Model Context Protocol)** allows agents to run locally or as distributed services.

- **Local Mode** (`USE_MCP=false`): Direct function calls, fast, good for dev
- **MCP Mode** (`USE_MCP=true`): Network calls to MCP servers, scalable, good for prod

**The same agent code works in both modes** via factory functions:

```python
from core.agents.agent_sdk.mcp_client import get_price_optimizer_client

# Factory returns either MCP client OR local function facade
tools = get_price_optimizer_client(use_mcp=None)  # None = read from env

# Call uniformly regardless of mode
result = await tools.get_product_info(sku="SKU-123")
```

#### 4. SSE Streaming for Real-Time UI

**Server-Sent Events (SSE)** push updates from backend to frontend in real-time.

**7 event types**:
1. `thinking` - LLM is processing
2. `agent` - Active agent name
3. `tool_call` - Tool execution (start/end)
4. `message` - Text deltas or final message
5. `thread_renamed` - Auto-generated title
6. `done` - Stream completion
7. `error` - Error details

**Frontend subscribes once**, backend pushes many events over single connection.

#### 5. Governance System

**Two agents enforce business rules**:

1. **AutoApplier**: Fast, lightweight, optimistic concurrency
2. **GovernanceExecutionAgent**: Enhanced states, WAL mode, detailed logging

**Guardrails**:
- `min_margin`: Reject prices below minimum profit margin (default: 12%)
- `max_delta`: Reject large price changes (default: 10%)
- `auto_apply`: Master toggle for autonomous application

**Every decision is logged** to `decision_log` table (immutable audit trail).

---

## Development Workflow

### Daily Development Loop

1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

2. **Activate environment**:
   ```bash
   venv\Scripts\activate  # Windows
   ```

3. **Run tests** (before making changes):
   ```bash
   pytest -v
   cd frontend && npm run test
   ```

4. **Make your changes** (see [Common Tasks](#common-tasks))

5. **Test your changes**:
   ```bash
   # Run specific test
   pytest tests/test_your_feature.py -v
   
   # Or smoke test
   python scripts/smoke_your_feature.py
   ```

6. **Format & lint**:
   ```bash
   # Python
   black .
   isort .
   flake8 .
   
   # TypeScript
   cd frontend
   npm run lint:fix
   npm run format
   ```

7. **Commit frequently** (local commits only):
   ```bash
   git add .
   git commit -m "feat: add feature X"
   ```

8. **Never push** without explicit instruction from user

### Testing Strategy

**3 levels of testing**:

1. **Unit Tests**: Fast, isolated, mock external dependencies
   - Location: `backend/tests/`, `frontend/src/**/*.test.tsx`
   - Run: `pytest` or `npm run test`

2. **Smoke Tests**: Quick integration checks, real databases
   - Location: `scripts/smoke_*.py`
   - Run: `python scripts/smoke_end_to_end.py`

3. **E2E Tests**: Full user workflows in browser
   - Location: `frontend/e2e/`
   - Run: `npm run test:e2e` (requires app running)

**Always test both**:
- ✅ LLM enabled (`OPENAI_API_KEY` set)
- ✅ LLM disabled (fallback heuristics)
- ✅ MCP mode (`USE_MCP=true`)
- ✅ Local mode (`USE_MCP=false`)

---

## Common Tasks

### Task 1: Add a New Agent

**Goal**: Create an autonomous agent that reacts to events.

**Steps**:

1. **Create agent file**:
   ```bash
   # Example: New inventory monitoring agent
   touch core/agents/inventory_monitor.py
   ```

2. **Implement agent class**:
   ```python
   # core/agents/inventory_monitor.py
   from core.agents.agent_sdk.bus_factory import get_bus
   from core.agents.agent_sdk.protocol import Topic
   
   class InventoryMonitorAgent:
       def __init__(self):
           self.running = False
       
       async def start(self):
           """Subscribe to events"""
           self.running = True
           
           async def on_price_update(payload):
               await self._check_inventory(payload)
           
           get_bus().subscribe(Topic.PRICE_UPDATE.value, on_price_update)
       
       async def _check_inventory(self, payload):
           """Business logic here"""
           sku = payload["product_id"]
           # Check inventory levels
           # Publish alert if low
           if inventory_low:
               await get_bus().publish(Topic.ALERT.value, {
                   "level": "warning",
                   "message": f"Low inventory for {sku}"
               })
       
       async def stop(self):
           self.running = False
   ```

3. **Add smoke test**:
   ```python
   # scripts/smoke_inventory_monitor.py
   import asyncio
   from core.agents.inventory_monitor import InventoryMonitorAgent
   
   async def main():
       agent = InventoryMonitorAgent()
       await agent.start()
       # Simulate events, verify behavior
       await agent.stop()
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

4. **Test**:
   ```bash
   python scripts/smoke_inventory_monitor.py
   
   # Check events were published
   Get-Content data\events.jsonl -Tail 10
   ```

### Task 2: Add a New API Endpoint

**Goal**: Expose backend functionality via REST API.

**Steps**:

1. **Define endpoint in router**:
   ```python
   # backend/routers/inventory.py
   from fastapi import APIRouter, Depends
   from backend.deps import get_repo, get_current_user
   
   router = APIRouter(prefix="/api/inventory", tags=["inventory"])
   
   @router.get("/{sku}")
   async def get_inventory(
       sku: str,
       repo=Depends(get_repo),
       user=Depends(get_current_user)
   ):
       """Get inventory level for a product"""
       inventory = repo.get_inventory(sku)
       if not inventory:
           raise HTTPException(status_code=404, detail="Not found")
       return inventory
   ```

2. **Register router**:
   ```python
   # backend/main.py
   from backend.routers import inventory
   
   app.include_router(inventory.router)
   ```

3. **Update OpenAPI spec**:
   ```bash
   python scripts/export_openapi.py
   ```

4. **Add unit test**:
   ```python
   # backend/tests/test_inventory_api.py
   from unittest.mock import patch
   from fastapi.testclient import TestClient
   
   def test_get_inventory():
       with patch("backend.routers.inventory.get_repo") as mock_repo:
           mock_repo.return_value.get_inventory.return_value = {"sku": "SKU-123", "qty": 50}
           
           client = TestClient(app)
           response = client.get("/api/inventory/SKU-123")
           
           assert response.status_code == 200
           assert response.json()["qty"] == 50
   ```

5. **Test**:
   ```bash
   pytest backend/tests/test_inventory_api.py -v
   ```

### Task 3: Add Frontend Feature

**Goal**: Display new data in the UI.

**Steps**:

1. **Create React Query hook**:
   ```typescript
   // frontend/src/hooks/useInventory.ts
   import { useQuery } from '@tanstack/react-query';
   import { api } from '@/lib/api/client';
   
   export function useInventory(sku: string) {
     return useQuery({
       queryKey: ['inventory', sku],
       queryFn: async () => {
         const res = await api.get(`/api/inventory/${sku}`);
         return res.data;
       }
     });
   }
   ```

2. **Create component**:
   ```typescript
   // frontend/src/components/inventory/InventoryBadge.tsx
   import { useInventory } from '@/hooks/useInventory';
   
   export function InventoryBadge({ sku }: { sku: string }) {
     const { data, isLoading } = useInventory(sku);
     
     if (isLoading) return <span>Loading...</span>;
     
     return (
       <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
         Stock: {data.qty}
       </span>
     );
   }
   ```

3. **Use in parent component**:
   ```typescript
   // frontend/src/components/products/ProductCard.tsx
   import { InventoryBadge } from '../inventory/InventoryBadge';
   
   export function ProductCard({ product }) {
     return (
       <div>
         <h3>{product.name}</h3>
         <InventoryBadge sku={product.sku} />
       </div>
     );
   }
   ```

4. **Test**:
   ```bash
   cd frontend
   npm run test -- InventoryBadge.test.tsx
   ```

### Task 4: Debug Event Flow

**Goal**: Understand why an event isn't triggering expected behavior.

**Steps**:

1. **Watch event log in real-time**:
   ```powershell
   Get-Content data\events.jsonl -Wait -Tail 20 | ForEach-Object {
       $_ | ConvertFrom-Json | ConvertTo-Json -Depth 10
   }
   ```

2. **Filter specific topic**:
   ```powershell
   Get-Content data\events.jsonl -Wait | Select-String "PRICE_PROPOSAL"
   ```

3. **Check agent subscriptions**:
   ```python
   # Add debug logging to agent
   async def on_proposal(payload):
       print(f"[DEBUG] Received proposal: {payload}")
       # ... rest of handler
   ```

4. **Verify event publishing**:
   ```python
   # In publishing agent
   print(f"[DEBUG] Publishing PRICE_PROPOSAL: {proposal}")
   await get_bus().publish(Topic.PRICE_PROPOSAL.value, proposal)
   ```

5. **Check event journal**:
   ```bash
   # Count events by topic
   Get-Content data\events.jsonl | ConvertFrom-Json | Group-Object topic | Select-Object Name, Count
   ```

---

## Debugging Guide

### Common Issues

#### Issue 1: "LLM provider unavailable"

**Symptoms**: Agents fall back to heuristics, `error` events in stream

**Diagnosis**:
```bash
# Check API keys in .env
cat .env | Select-String "API_KEY"

# Test LLM connection
python scripts/debug/test_llm_connection.py
```

**Solutions**:
- Verify API key is valid and not expired
- Check API key has sufficient credits
- Try different provider (OpenAI → OpenRouter → Gemini)

#### Issue 2: "Event not triggering agent"

**Symptoms**: Event published but subscriber doesn't react

**Diagnosis**:
```bash
# Check events.jsonl for published event
Get-Content data\events.jsonl -Tail 50 | Select-String "YOUR_TOPIC"

# Add logging to subscriber
# In agent code:
print(f"[DEBUG] Subscribing to {Topic.YOUR_TOPIC.value}")
```

**Solutions**:
- Ensure agent `start()` method was called
- Check topic name matches exactly (case-sensitive)
- Verify event payload matches expected schema
- Check for exceptions in subscriber callback (silent failures)

#### Issue 3: "Database locked"

**Symptoms**: `sqlite3.OperationalError: database is locked`

**Diagnosis**:
```python
# Check if WAL mode enabled
import sqlite3
conn = sqlite3.connect("app/data.db")
print(conn.execute("PRAGMA journal_mode").fetchone())
```

**Solutions**:
- Enable WAL mode: `PRAGMA journal_mode=WAL`
- Increase busy timeout: `PRAGMA busy_timeout=5000`
- Use connection pooling
- Avoid long-running transactions

#### Issue 4: "SSE stream hangs"

**Symptoms**: Frontend shows "Thinking..." indefinitely, no response

**Diagnosis**:
```javascript
// Check browser Network tab -> Event Stream
// Look for last event received

// Check backend logs for exceptions
```

**Solutions**:
- Always emit `done` or `error` event to close stream
- Flush after each SSE event: `await response.send()`
- Check LLM client timeout (default: 30s)
- Verify watchdog timer in frontend (25s)

### Debugging Tools

**Backend**:
- `scripts/debug/` - Debugging utilities
- `data/events.jsonl` - Event audit trail
- FastAPI docs - http://localhost:8000/docs (test endpoints)

**Frontend**:
- React DevTools - Inspect component state
- TanStack Query DevTools - Monitor API calls
- Browser Network tab - View SSE events

**Database**:
- DB Browser for SQLite - GUI for database inspection
- `sqlite3 app/data.db` - Command-line access

---

## Best Practices

### Code Style

**Python**:
- ✅ `snake_case` for functions/variables
- ✅ `PascalCase` for classes
- ✅ Type hints everywhere (mypy strict mode)
- ✅ No comments (code should be self-documenting)
- ✅ Use `HTTPException` in API endpoints
- ✅ Max line length: 120 characters

**TypeScript**:
- ✅ `camelCase` for functions/variables
- ✅ `PascalCase` for components/types
- ✅ Strong typing (avoid `any`)
- ✅ Tailwind CSS only (no custom CSS files)
- ✅ Extract complex logic to custom hooks

### Architecture Principles

1. **Event-Driven**: Use event bus for agent communication, never direct function calls
2. **Idempotent**: Events may be replayed, design for duplicate handling
3. **Fail-Safe**: Always implement fallback heuristics for LLM unavailability
4. **Observable**: Log important events, track metrics, enable debugging
5. **Async-First**: Use async/await, avoid blocking operations
6. **Stateless**: Agents should be stateless where possible, state in database

### Performance Tips

1. **Database**:
   - Enable WAL mode for concurrent reads
   - Use indexes on frequently queried columns
   - Batch inserts when possible
   - Avoid SELECT * (specify columns)

2. **LLM Calls**:
   - Cache results when possible
   - Use streaming for long responses
   - Set appropriate `max_tokens` limits
   - Implement retry with exponential backoff

3. **Event Bus**:
   - Never block in event callbacks
   - Offload heavy work to background threads
   - Use typed dataclasses for validation
   - Publish events after database commits

### Security Checklist

- [ ] **Never commit secrets** (check `.env` is in `.gitignore`)
- [ ] **Validate all inputs** (use Pydantic models)
- [ ] **Require authentication** on sensitive endpoints (use `Depends(get_current_user)`)
- [ ] **Sanitize SQL** (use ORM, avoid raw queries)
- [ ] **Rate limit API** endpoints
- [ ] **Audit dependency vulnerabilities** (`npm audit`, `pip-audit`)

### Git Workflow

1. **Commit frequently** (every logical unit of work)
2. **Use conventional commits**:
   - `feat: add inventory monitoring agent`
   - `fix: resolve database lock issue`
   - `docs: update API reference`
   - `test: add smoke test for governance`
3. **Never push** without user instruction
4. **No branches** (all work on main)
5. **Explain intermediate/advanced git** actions to user

---

## Next Steps

### Recommended Learning Path

**Week 1**: Understand fundamentals
- [ ] Read `suggestions_for_agents.md` (full architecture)
- [ ] Explore `docs/QUICK_REFERENCE.md` (cheat sheets)
- [ ] Run all smoke tests (`scripts/smoke_*.py`)
- [ ] Watch `data/events.jsonl` during app usage

**Week 2**: Make small changes
- [ ] Add new event topic
- [ ] Create simple agent that logs events
- [ ] Add new API endpoint
- [ ] Build simple UI component

**Week 3**: Build features
- [ ] Implement LLM-powered agent
- [ ] Add streaming endpoint
- [ ] Integrate MCP tool
- [ ] Write comprehensive tests

**Week 4**: Master the system
- [ ] Contribute to core infrastructure
- [ ] Optimize performance bottlenecks
- [ ] Enhance observability
- [ ] Mentor other developers

### Resources

- **Architecture**: `suggestions_for_agents.md`
- **Quick Reference**: `docs/QUICK_REFERENCE.md`
- **Diagrams**: `docs/ARCHITECTURAL_DIAGRAMS.md`
- **API Spec**: `openapi.json`
- **Event Log**: `data/events.jsonl`
- **Codebase Overview**: `docs/codebase_overview.md`

### Getting Help

If stuck, check in this order:
1. `docs/QUICK_REFERENCE.md` - Common patterns
2. `data/events.jsonl` - Event flow debugging
3. `scripts/debug/` - Debugging utilities
4. Ask senior developer

---

## Welcome Aboard!

You're now equipped to contribute to the Dynamic Pricing AI system. Remember:

- **Start small**: Make incremental changes
- **Test thoroughly**: Unit → Smoke → E2E
- **Commit frequently**: Local commits only
- **Ask questions**: Better to clarify than assume

Happy coding! 🚀
