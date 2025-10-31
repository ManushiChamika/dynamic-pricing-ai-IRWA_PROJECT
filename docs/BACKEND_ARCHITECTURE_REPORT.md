# Backend Architecture Report
## Dynamic Pricing AI System - Comprehensive Analysis

**Document Generated:** October 19, 2025  
**Project:** FluxPricer - Dynamic Pricing System with AI  
**Stack:** Python 3.x + FastAPI + SQLite + LLM Integration

---

## Executive Summary

The backend is a sophisticated **multi-agent autonomous system** designed for dynamic pricing with real-time market monitoring and AI-driven decision-making. It combines:

- **FastAPI REST API** for frontend/external integration
- **Multi-agent architecture** with specialized agents for pricing, market data collection, and alerting
- **Event-driven bus system** for inter-agent communication
- **LLM integration** for autonomous decision-making
- **SQLite databases** for persistence (auth, chat, market data, pricing)
- **Real-time chat interface** with streaming responses
- **Autonomous workflows** for price optimization and market intelligence

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React/TS)                    │
└────────────────┬────────────────────────────────────────────┘
                 │ REST API + WebSocket (SSE)
┌────────────────▼────────────────────────────────────────────┐
│                  FASTAPI SERVER (8000)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routers: Auth | Threads | Messages | Prices | etc │  │
│  │  Middleware: CORS | Auth | Chat Auth               │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┴──────────────┬──────────────────┐
    │                           │                  │
┌───▼──────────┐    ┌───────────▼──┐    ┌─────────▼──┐
│   Agent Bus  │    │  Databases   │    │    LLM     │
│  (in-process)│    │   Layer      │    │  Clients   │
└───┬──────────┘    └──────┬───────┘    └────────────┘
    │                      │
    │            ┌─────────┴─────────┐
    │            │                   │
    ▼            ▼                   ▼
  Agents    SQLite DBs         Ext. Services
```

### 1.2 Core Components

| Component | Purpose | Status |
|-----------|---------|--------|
| FastAPI App | HTTP/REST API server | ✅ Core |
| Router Layer | API endpoints (auth, chat, pricing, alerts) | ✅ Active |
| Agent Bus | Event broker for inter-agent communication | ✅ In-memory |
| LLM Client | Abstract layer for LLM provider management | ✅ Configured |
| Database Layer | SQLite persistence (auth, chat, pricing) | ✅ Active |
| Autonomous Agents | Self-driving market monitoring & optimization | ✅ Running |

---

## 2. Agent Architecture

The system uses **multi-agent autonomous orchestration** with clear responsibilities:

### 2.1 Agent Types

#### A. **User Interaction Agent** (`core/agents/user_interact/`)
**Responsibility:** Handle user queries through chat interface

- **Entry Point:** REST endpoint `/api/threads/{id}/messages/stream`
- **Capabilities:**
  - Tool invocation (check_stale_market_data, scan_for_alerts, optimize_price, etc.)
  - LLM-powered conversational responses
  - Tool schema integration for dynamic capability discovery
  - Memory/context management across conversation threads

- **Key Methods:**
  - `stream_response()` - Real-time SSE streaming
  - `execute_tool_call()` - Run tools dynamically based on LLM decisions

- **Tools Available:**
  - `list_inventory_items` - Query product catalog
  - `get_inventory_item` - Single product lookup
  - `list_market_data` - Market research data
  - `check_stale_market_data` - Identify outdated data (NEW)
  - `scan_for_alerts` - Retrieve pricing incidents
  - `optimize_price` - Trigger price optimization for a SKU
  - `list_pricing_list` - Current market pricing
  - `list_price_proposals` - Recent price proposals

#### B. **Price Optimizer Agent** (`core/agents/price_optimizer/`)
**Responsibility:** Autonomous price optimization workflow

- **Trigger:** Manual invocation or scheduled optimization requests
- **Workflow:**
  1. Fetch product info from inventory
  2. Gather competitive market intelligence
  3. Select optimal pricing algorithm:
     - `rule_based` - Conservative, competitor-average-based
     - `ml_model` - Predictive based on historical patterns
     - `profit_maximization` - Aggressive margin optimization
  4. Validate constraints (min/max price, margin thresholds)
  5. Publish price proposal to event bus

- **Key Classes:**
  - `PricingOptimizerAgent` - Main orchestrator
  - `LLMBrain` - LLM-powered algorithm selection
  - `optimize()` - Algorithm execution engine

- **Database:** `app/data.db` (price_proposals table)

#### C. **Data Collector Agent** (`core/agents/data_collector/`)
**Responsibility:** Proactive market data freshness monitoring

- **Autonomy:** Runs continuously, checks data age every 180 seconds
- **Workflow:**
  1. Identify products with stale market data (>60 min old)
  2. Check for already-running collection jobs
  3. Start new collection jobs for stale products
  4. Monitor success rates and job statuses

- **Connectors:**
  - `web_scraper.py` - Real web scraping (production)
  - `mock.py` - Mock data for development

- **Tools:**
  - `start_collection_job()` - Begin market fetch
  - `get_stale_products()` - Identify old data
  - `get_active_jobs()` - Check in-progress collections

- **Database:** `app/data.db` (market_data table)

#### D. **Alert Engine / Notification Agent** (`core/agents/alert_service/`)
**Responsibility:** Real-time anomaly detection and alerting

- **Triggers:** 
  - PRICE_PROPOSAL events (when prices are proposed)
  - MARKET_TICK events (periodic market updates)

- **Detection Rules:**
  - Low margin detection (< 5%)
  - Negative margins (selling at loss)
  - Price anomalies
  - Data quality issues (empty proposals, malformed events)

- **Alert Sinks:** Multiple delivery channels
  - UI alerts (websocket/SSE to frontend)
  - Slack webhook integration
  - Email notifications
  - Database persistence

- **Database:** `app/data.db` (incidents table)

### 2.2 Agent Communication Architecture

```
┌─────────────────────────────────────────────┐
│           Event Bus (In-Memory)             │
│  (BUS_BACKEND: inproc | redis)              │
└────────┬──────────────────────────┬─────────┘
         │                          │
    ┌────▼──────┐          ┌───────▼────┐
    │  Subscribe │          │  Publish   │
    │  to Topics │          │  Topics    │
    └────┬───────┘          └────┬───────┘
         │                       │
    ┌────┼───────────────────────┼────┐
    │    │                       │    │
  ┌─▼──┐│ ┌──────────────────┐ ┌▼──┐ │
  │Agent││ │    Topics        │ │Agent││
  │  1  ││ ├──────────────────┤ │  2  │
  └────┘│ │ MARKET_TICK      │ └────┘
        │ │ PRICE_PROPOSAL   │
        │ │ ALERT            │
        │ │ JOB_START        │
        │ │ JOB_DONE         │
        │ └──────────────────┘
        └────────────────────────┘

Topics (core/agents/agent_sdk/protocol.py):
- MARKET_TICK: New market data available
- PRICE_PROPOSAL: Price optimization complete
- ALERT: Anomalies detected
- JOB_START: Collection job started
- JOB_DONE: Collection job completed
```

### 2.3 Agent Initialization & Lifespan

**In `backend/main.py` FastAPI lifespan:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()              # Auth database
    init_chat_db()         # Chat database
    cleanup_empty_threads()
    
    await alert_api.start()         # AlertEngine starts
    await pricing_optimizer.start()  # PricingOptimizerAgent starts
    
    yield  # App running
    
    # Shutdown (cleanup)
```

All agents start independently and subscribe to the event bus.

---

## 3. API Layer Architecture

### 3.1 Router Structure

Located in `backend/routers/`:

| Router | Endpoints | Purpose |
|--------|-----------|---------|
| `auth.py` | `/api/login`, `/api/register`, `/api/logout` | User authentication |
| `settings.py` | `/api/settings` | User preferences, LLM model selection |
| `threads.py` | `/api/threads` (CRUD) | Chat thread management |
| `messages.py` | `/api/messages` (GET list) | Message history |
| `streaming.py` | `/api/threads/{id}/messages/stream` | **Real-time chat with SSE** |
| `prices.py` | `/api/prices/*` | Pricing data endpoints |
| `catalog.py` | `/api/catalog/*` | Product catalog management |
| `alerts.py` | `/api/alerts/*` | Alert management & status |

### 3.2 Authentication Middleware

**Middleware Stack:**

```python
1. CORSMiddleware
   - Allow: localhost:* (dev) / configured origins (prod)
   - Credentials enabled for cookies/auth headers

2. ChatAuthMiddleware
   - Optional login enforcement (UI_REQUIRE_LOGIN env var)
   - Token validation for /api/threads and /api/messages routes
   - Support for: Bearer tokens, Query params, Cookies
```

### 3.3 Request/Response Flow

**Streaming Chat Request Example:**

```
POST /api/threads/{thread_id}/messages/stream
├─ Header: Authorization: Bearer <token>
├─ Body: {"content": "Check stale data", "user_name": "user"}
│
├─ Validation
│  └─ Token validation → UserID
│
├─ UserInteractionAgent
│  ├─ Build context (memory from thread)
│  ├─ Call LLM with tool schemas
│  ├─ LLM selects tool (e.g., check_stale_market_data)
│  ├─ Execute tool → Get results
│  ├─ Format response (Markdown → HTML tables)
│  └─ Stream via SSE
│
└─ Response: text/event-stream
   ├─ event: chunk
   │  data: "Found 5 stale products..."
   ├─ event: tool_call
   │  data: {tool: "check_stale_market_data", result: {...}}
   └─ event: done
```

---

## 4. Database Architecture

### 4.1 Database Files

| Database | Location | Purpose | Tables |
|----------|----------|---------|--------|
| **auth.db** | `data/auth.db` | User authentication | users, session_tokens |
| **chat.db** | `data/chat.db` | Conversation history | threads, messages, summaries |
| **data.db** | `app/data.db` | Business data | product_catalog, market_data, price_proposals, incidents, pricing_list |

### 4.2 Core Tables in `app/data.db`

**A. product_catalog**
```sql
├─ sku (PRIMARY KEY)
├─ title
├─ currency
├─ current_price
├─ cost
├─ stock
├─ updated_at
└─ (market/source specific fields)
```

**B. market_data**
```sql
├─ id (PRIMARY KEY)
├─ product_name
├─ price
├─ features
├─ update_time (CRITICAL - used for staleness check)
└─ source/competitor info
```

**C. price_proposals**
```sql
├─ id (PRIMARY KEY)
├─ sku (FOREIGN KEY → product_catalog)
├─ proposed_price
├─ current_price
├─ margin
├─ algorithm (rule_based|ml_model|profit_maximization)
├─ ts (timestamp)
└─ metadata
```

**D. incidents** (Alerts)
```sql
├─ id (PRIMARY KEY)
├─ sku
├─ title (alert name)
├─ severity (critical|warning|info)
├─ status (OPEN|ACKNOWLEDGED|RESOLVED)
├─ created_at
└─ details (JSON event data)
```

**E. pricing_list**
```sql
├─ product_name
├─ optimized_price
├─ last_update
└─ reason
```

### 4.3 Database Access Patterns

All database access routes through **abstraction layers:**

- **Agent Layer**: `core/agents/*/repo.py` (Repository pattern)
- **API Layer**: `backend/routers/*.py` (SQL queries with ORM)
- **Core Utilities**: `core/chat_db.py`, `core/auth_db.py` (SQLAlchemy models)

---

## 5. LLM Integration & Tool Calling

### 5.1 LLM Provider Architecture

**Provider Management:**

```python
core/agents/llm_client.py
├─ LLMClient (Abstract)
│  ├─ get_llm_client()      # Factory function
│  ├─ is_available()
│  ├─ call_with_tools()     # LLM + tool schema support
│  └─ extract_tool_calls()  # Parse LLM responses
│
└─ Supported Providers:
   ├─ OpenAI (GPT-4, GPT-3.5)
   ├─ OpenRouter (multiple models)
   └─ Custom (configurable base URL)
```

**Configuration via Environment Variables:**

```env
# OpenRouter (Recommended for free tier)
OPENROUTER_API_KEY=sk-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=deepseek/deepseek-r1-0528:free

# Or OpenAI direct
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 5.2 Tool Schema System

**Tool Schema Definition:**

```python
# core/agents/user_interact/tool_schemas.py
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "check_stale_market_data",
            "description": "Check market data older than threshold",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold_minutes": {
                        "type": "integer",
                        "description": "Age threshold in minutes",
                        "default": 60
                    }
                }
            }
        }
    },
    # ... more tools
]
```

**Tool Execution Flow:**

```
1. LLM receives tool schemas
2. LLM decides which tool(s) to call based on user query
3. LLM returns function_calls array
4. Backend extracts tool name + arguments
5. TOOLS_MAP[tool_name]() executes the function
6. Result sent back to LLM for interpretation
7. LLM formats response for user
```

**Tool Result Processing:**

```python
def execute_tool_call(tool_name: str, kwargs: dict) -> dict:
    """Execute a tool and return standardized result."""
    if tool_name not in TOOLS_MAP:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        result = TOOLS_MAP[tool_name](**kwargs)
        return result
    except Exception as e:
        return {"error": str(e)}
```

---

## 6. Event-Driven Architecture

### 6.1 Event Bus System

**Bus Configuration:**

```python
# core/config.py
BUS_BACKEND: str              # "inproc" | "redis"
BUS_REDIS_URL: str           # "redis://localhost:6379/0"
BUS_MAX_QUEUE_SIZE: int      # Default: 1000
BUS_CONCURRENCY_LIMIT: int   # Default: 10
```

**Bus Factory:**

```python
# core/agents/agent_sdk/bus_factory.py
from .protocol import Topic

bus = get_bus()

# Publishing
await bus.publish(Topic.PRICE_PROPOSAL.value, {
    "proposal_id": "...",
    "sku": "LAPTOP-001",
    "proposed_price": 899.99
})

# Subscribing
bus.subscribe(Topic.PRICE_PROPOSAL.value, on_price_proposal_handler)
```

### 6.2 Event Topics

```python
class Topic(Enum):
    MARKET_TICK = "market.tick"              # New market data
    PRICE_PROPOSAL = "price.proposal"        # Price optimization done
    ALERT = "alert"                          # Anomaly detected
    JOB_START = "job.start"                  # Collection started
    JOB_DONE = "job.done"                    # Collection completed
```

### 6.3 Event Validation

```python
# core/events/schemas.py
REQUIRED_KEYS = {
    "price.proposal": ("proposal_id", "product_id", "proposed_price"),
    "market.fetch.done": ("request_id", "job_id", "status", "tick_count"),
    # ... validated before publishing
}
```

---

## 7. Real-Time Chat Streaming

### 7.1 Server-Sent Events (SSE) Implementation

**Endpoint:** `POST /api/threads/{thread_id}/messages/stream`

**Response Format:**

```
text/event-stream

event: chunk
data: "Found 5 stale products"

event: tool_call
data: {"tool": "check_stale_market_data", "args": {"threshold_minutes": 60}}

event: tool_result
data: {"stale_count": 5, "total_count": 42}

event: chunk
data: "\n\nDetails:\n"

event: done
data: {"status": "complete", "tokens_in": 123, "tokens_out": 456}
```

### 7.2 Streaming Pipeline

```
User Query
    ↓
[Thread ID] → Load conversation context
    ↓
UserInteractionAgent.stream_response()
    ├─ Call LLM with tools (via OpenRouter/OpenAI)
    ├─ Stream chunks as they arrive
    ├─ Parse LLM tool calls
    ├─ Execute tools
    ├─ Feed results back to LLM
    ├─ Format response (Markdown tables fix)
    └─ Emit SSE events
    ↓
Frontend (React) receives SSE
    ├─ Accumulate chunks
    ├─ Parse tool calls
    ├─ Render Markdown (with table support)
    └─ Display in UI
```

### 7.3 Markdown Table Rendering

**Issue Fixed:** Tables in chat were rendering as raw text with pipe separators.

**Solution** (`frontend/src/components/chat/MarkdownRenderer.tsx`):

```typescript
function cleanMarkdownTables(markdown: string): string {
    // Process table separators: reduce excessive dashes to standard
    return markdown.replace(/\|[\s-:]{3,}(?:\|[\s-:]{3,})+\|/g, (match) => {
        const cells = match.split('|')
            .filter(cell => cell.length > 0)
            .map(cell => {
                const trimmed = cell.trim()
                if (trimmed.startsWith(':') && trimmed.endsWith(':')) 
                    return ':-:'  // center
                if (trimmed.startsWith(':')) 
                    return ':--'   // left
                if (trimmed.endsWith(':')) 
                    return '--:'   // right
                return '---'       // no alignment
            })
        return '|' + cells.join('|') + '|'
    })
}
```

---

## 8. Configuration & Environment

### 8.1 Core Configuration (`core/config.py`)

**Centralized config management with validation:**

```python
class Config:
    # Environment
    environment: str                    # "development" | "production"
    debug: bool
    
    # Authentication
    auth_secret: str                   # MCP_AUTH_SECRET (required)
    token_expiry_seconds: int          # Default: 300 (5 min)
    auth_metrics_enabled: bool
    
    # Bus/Messaging
    bus_backend: str                   # "inproc" | "redis"
    bus_redis_url: str
    bus_max_queue_size: int            # Default: 1000
    bus_concurrency_limit: int         # Default: 10
    
    # Database
    database_url: str                  # SQLite path
    
    # LLM
    openai_api_key: str
    openai_base_url: str
    
    # Service
    service_host: str                  # Default: 0.0.0.0
    service_port: int                  # Default: 8000
    
    # Logging
    log_level: str                     # INFO | DEBUG | WARNING
    log_structured: bool
```

### 8.2 Validation Rules

Config validates on startup:
- ✅ Auth secret minimum 32 characters
- ✅ Bus backend in ["inproc", "redis"]
- ✅ Token expiry 1-86400 seconds
- ✅ Queue size 1-100000
- ✅ Concurrency limit 1-1000
- ✅ Valid log levels

---

## 9. Autonomous Workflows

### 9.1 Price Optimization Workflow

**Triggered by:** Manual API call or scheduled task

```
1. User/API → optimize_price(sku="LAPTOP-001")
    ↓
2. PricingOptimizerAgent.process_full_workflow()
    ├─ Step 1: Get product info
    │   └─ Query product_catalog
    ├─ Step 2: Get market intelligence
    │   └─ Query market_data (competitors)
    ├─ Step 3: Select algorithm
    │   ├─ LLM decides: rule_based|ml_model|profit_maximization
    │   └─ Or fallback to heuristic
    ├─ Step 4: Run pricing algorithm
    │   └─ Apply formulas/ML model
    ├─ Step 5: Validate constraints
    │   ├─ Min price >= cost
    │   ├─ Max price <= market ceiling
    │   └─ Margin constraints
    ├─ Step 6: Publish price proposal
    │   ├─ Insert into price_proposals table
    │   ├─ Emit PRICE_PROPOSAL event
    │   └─ AlertEngine receives event
    │
    └─ Response: {"status": "ok", "proposed_price": 899.99}

3. AlertEngine detects proposal
    ├─ Evaluate against rules
    ├─ Check for anomalies (negative margin, etc.)
    └─ Create incident if triggered

4. Auto-applier (if enabled)
    └─ Apply price to product_catalog
```

### 9.2 Data Collection Workflow

**Running autonomously every 180 seconds:**

```
1. DataCollectorAgent._autonomous_loop()
    ├─ Call get_stale_products(threshold=60 minutes)
    ├─ Get active collection jobs
    ├─ For each stale product (prioritized)
    │   ├─ Skip if job already running
    │   ├─ Call start_collection_job(sku, market, connector)
    │   ├─ Job ID returned
    │   └─ Emit JOB_START event
    │
    └─ Monitor job completions

2. Market Data Collection Job
    ├─ Connector selected: web_scraper|mock
    ├─ Fetch competitor prices from sources
    ├─ Store in market_data table
    ├─ Update update_time column
    └─ Emit JOB_DONE event

3. Data available for optimization
    └─ Price optimizer can now see fresh data
```

### 9.3 Alert Detection Workflow

**Real-time monitoring:**

```
1. Event published to bus (PRICE_PROPOSAL | MARKET_TICK)
    ↓
2. AlertEngine.on_event()
    ├─ Load configured rules
    ├─ Evaluate rules (RuleRuntime)
    ├─ Detect anomalies via LLM (if available)
    └─ Create alert if triggered
    ↓
3. Alert stored & distributed
    ├─ Insert into incidents table
    ├─ Publish ALERT event
    └─ Send via alert sinks:
       ├─ UI (websocket/SSE)
       ├─ Slack webhook
       ├─ Email
       └─ Webhook

4. User sees alert in UI
    └─ Can acknowledge or resolve
```

---

## 10. Data Flow Diagrams

### 10.1 User Query → Response Flow

```
┌──────────────┐
│ User sends   │
│ chat message │
└──────┬───────┘
       │ POST /api/threads/{id}/messages/stream
       │ {"content": "Check stale data"}
       ▼
┌────────────────────────────────────────────┐
│ API Layer (streaming.py)                   │
│ ├─ Authentication check                    │
│ ├─ Load thread context (memory)            │
│ └─ Create UserInteractionAgent             │
└────────┬─────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ UserInteractionAgent.stream_response()     │
│ ├─ Call LLM API with:                      │
│ │  ├─ User message                         │
│ │  ├─ Tool schemas                         │
│ │  └─ Conversation history                 │
│ └─ LLM decides: "Use check_stale_market..." │
└────────┬─────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ Tool Execution                             │
│ ├─ Execute: check_stale_market_data()      │
│ │  ├─ Query market_data table              │
│ │  │  WHERE age > 60 minutes               │
│ │  └─ Return stale_items list              │
│ └─ Result: {"stale_count": 5, ...}         │
└────────┬─────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ LLM Interprets Result                      │
│ ├─ Format response with data               │
│ ├─ Generate Markdown table                 │
│ └─ Return formatted response                │
└────────┬─────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ SSE Stream Response                        │
│ ├─ event: chunk                            │
│ │  data: "Found 5 stale products..."       │
│ ├─ event: chunk (table markdown)           │
│ │  data: "| Product | Age |..."            │
│ └─ event: done                             │
│    data: {"tokens_in": 120, ...}           │
└────────┬─────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│ Frontend (React)                           │
│ ├─ Receives SSE chunks                     │
│ ├─ Parses Markdown                         │
│ ├─ Renders table in UI                     │
│ └─ Display to user                         │
└────────────────────────────────────────────┘
```

### 10.2 Autonomous Price Optimization

```
┌──────────────────┐
│  [Trigger]       │
│  API call OR     │
│  scheduled       │
└────────┬─────────┘
         │
         ▼
    ┌────────────────────────┐
    │ PricingOptimizerAgent  │
    │ .process_full_workflow │
    └────────┬───────────────┘
             │
    ┌────────▼──────────────────────┐
    │ 1. Get Product Info            │
    │    SELECT * FROM               │
    │    product_catalog WHERE sku=? │
    └────────┬──────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │ 2. Get Market Data             │
    │    SELECT price FROM           │
    │    market_data ORDER BY...     │
    └────────┬──────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │ 3. LLM Algorithm Selection     │
    │    (or heuristic fallback)     │
    │    • rule_based                │
    │    • ml_model                  │
    │    • profit_maximization       │
    └────────┬──────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │ 4. Run Pricing Algorithm       │
    │    Compute optimal price       │
    │    price = f(cost, market...)  │
    └────────┬──────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │ 5. Validate Constraints        │
    │    ✓ price >= cost             │
    │    ✓ price <= ceiling          │
    │    ✓ margin >= threshold       │
    └────────┬──────────────────────┘
             │
    ┌────────▼────────────────────────┐
    │ 6. Publish Price Proposal        │
    │    ├─ INSERT price_proposals     │
    │    └─ Emit PRICE_PROPOSAL event │
    └────────┬───────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │ Event Bus                      │
    └────────┬──────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │ AlertEngine (listening)        │
    │ ├─ Evaluate rules              │
    │ ├─ Check for anomalies         │
    │ └─ Create incidents if needed  │
    └────────┬──────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │ Alert Sinks                    │
    │ ├─ UI notification             │
    │ ├─ Slack webhook               │
    │ ├─ Email notification          │
    │ └─ Database (incidents table)  │
    └────────────────────────────────┘
```

---

## 11. Code Organization

### 11.1 Directory Structure

```
backend/
├── routers/                    # FastAPI route handlers
│   ├── auth.py                # Login, register, logout
│   ├── threads.py             # Thread CRUD
│   ├── messages.py            # Message retrieval
│   ├── streaming.py           # SSE chat streaming
│   ├── prices.py              # Pricing endpoints
│   ├── catalog.py             # Catalog management
│   ├── alerts.py              # Alert endpoints
│   ├── settings.py            # User settings
│   └── utils.py               # Shared utilities
├── main.py                    # FastAPI app definition
├── test_*.py                  # API tests
└── __init__.py

core/
├── agents/                    # Multi-agent system
│   ├── user_interact/         # Chat interface agent
│   │   ├── user_interaction_agent.py  # Main agent
│   │   ├── tools.py           # Tool implementations
│   │   ├── tool_schemas.py    # Tool definitions
│   │   └── prompts.py         # System prompts
│   ├── price_optimizer/       # Price optimization
│   │   ├── agent.py           # Orchestrator
│   │   ├── optimizer.py       # Algorithm engine
│   │   ├── algorithms.py      # Pricing algorithms
│   │   ├── llm_brain.py       # LLM decision-making
│   │   └── tools.py           # Optimization tools
│   ├── data_collector/        # Market data collection
│   │   ├── agent.py           # Autonomous collector
│   │   ├── collector.py       # Collection engine
│   │   ├── repo.py            # Data repository
│   │   ├── connectors/        # Data source connectors
│   │   │   ├── web_scraper.py # Production scraper
│   │   │   └── mock.py        # Mock data
│   │   ├── tools.py           # Collector tools
│   │   └── mcp_server.py      # MCP integration
│   ├── alert_service/         # Alerting system
│   │   ├── engine.py          # Alert processing
│   │   ├── repo.py            # Alert persistence
│   │   ├── rules.py           # Rule engine
│   │   ├── detectors.py       # Anomaly detectors
│   │   ├── schemas.py         # Data models
│   │   ├── sinks/             # Alert delivery
│   │   │   ├── ui.py          # UI notifications
│   │   │   ├── slack.py       # Slack webhooks
│   │   │   ├── email.py       # Email
│   │   │   └── webhook.py     # Generic webhooks
│   │   ├── tools.py           # Alert tools
│   │   └── api.py             # Alert API
│   ├── agent_sdk/             # Agent framework
│   │   ├── protocol.py        # Event topic definitions
│   │   ├── bus_factory.py     # Event bus creation
│   │   ├── mcp_client.py      # MCP client
│   │   ├── activity_log.py    # Tracing
│   │   ├── auth.py            # MCP authentication
│   │   └── health_tools.py    # System health
│   ├── supervisor.py          # Workflow orchestrator
│   ├── chat_executor.py       # Chat execution
│   ├── llm_client.py          # LLM provider abstraction
│   ├── llm_provider_manager.py # Provider management
│   ├── base_chat_handler.py   # Base handler
│   ├── policy_guard.py        # Policy enforcement
│   ├── auto_applier.py        # Automatic price application
│   ├── governance_execution_agent.py  # Governance
│   ├── market_collector.py    # Legacy collector
│   └── __init__.py
├── evaluation/                # Performance evaluation
│   ├── evaluation_engine.py   # Metrics calculation
│   ├── performance_monitor.py # Monitoring
│   └── metrics.py             # Metric definitions
├── events/                    # Event system
│   ├── journal.py             # Event logging
│   └── schemas.py             # Event validation
├── observability/             # Observability
│   └── logging.py             # Structured logging
├── auth_db.py                 # Auth database models
├── auth_service.py            # Authentication service
├── chat_db.py                 # Chat database models
├── config.py                  # Configuration management
├── payloads.py                # Request/response DTOs
└── __init__.py
```

### 11.2 Key File Responsibilities

| File | Lines | Responsibility |
|------|-------|-----------------|
| `core/agents/user_interact/user_interaction_agent.py` | ~400 | LLM chat orchestration, tool invocation |
| `core/agents/price_optimizer/agent.py` | ~300 | Price optimization workflow |
| `core/agents/alert_service/engine.py` | ~250 | Alert detection & publishing |
| `core/agents/data_collector/agent.py` | ~200 | Autonomous data collection |
| `backend/routers/streaming.py` | ~180 | SSE chat streaming |
| `core/config.py` | ~191 | Configuration validation |
| `core/chat_db.py` | ~200+ | Chat database models |

---

## 12. Integration Points

### 12.1 Frontend Integration

**REST API Contract:**

```
Authentication:
- POST /api/login
- POST /api/register  
- POST /api/logout

Chat Interface:
- POST /api/threads                    # Create
- GET /api/threads                     # List
- GET /api/threads/{id}/messages       # Get history
- POST /api/threads/{id}/messages/stream    # Chat (SSE)
- PATCH /api/threads/{id}              # Update title

Settings:
- GET /api/settings
- POST /api/settings                   # Update user prefs

Pricing:
- GET /api/prices/current
- GET /api/prices/history
- POST /api/prices/optimize/{sku}

Catalog:
- GET /api/catalog
- POST /api/catalog
- DELETE /api/catalog/{sku}

Alerts:
- GET /api/alerts
- POST /api/alerts/{id}/acknowledge
- POST /api/alerts/{id}/resolve
```

### 12.2 External Service Integration

**OpenRouter/OpenAI LLM:**
- Authentication via API key
- Tool calling for autonomous agents
- Streaming responses for chat

**Slack Webhooks:**
- Send alerts to Slack channels
- Configured in alert_service/sinks/slack.py

**Email Services:**
- Alert notifications via SMTP
- Configured in alert_service/sinks/email.py

### 12.3 MCP (Model Context Protocol)

**MCP Server:**
- `core/agents/data_collector/mcp_server.py`
- Exposes collection jobs as MCP tools
- Used by agents to coordinate via MCP

**MCP Client:**
- `core/agents/agent_sdk/mcp_client.py`
- Connects to data collector MCP server
- Calls start_collection(), get_job_status()

---

## 13. Performance & Scalability

### 13.1 Concurrency Management

**Agent Concurrency:**
```python
# core/config.py
bus_concurrency_limit = 10  # Max concurrent async operations
```

**Database Connection Pooling:**
- SQLAlchemy with configurable pool size
- SQLite by default (single process)
- Redis bus optional for distributed setup

**Streaming Response Handling:**
- SSE (Server-Sent Events) for real-time updates
- Non-blocking async I/O for LLM calls
- Token streaming from LLM API

### 13.2 Monitoring & Observability

**Structured Logging:**
```python
# core/observability/logging.py
- Level-based filtering (DEBUG|INFO|WARNING|ERROR)
- Structured format with metadata
- Function/line number tracking
```

**Activity Tracing:**
```python
# core/agents/agent_sdk/activity_log.py
- Trace ID generation
- Event logging with context
- Redaction of sensitive data
```

**Performance Metrics:**
```python
# core/evaluation/metrics.py
- Token usage tracking
- API call counters
- Cost calculation per LLM provider
```

### 13.3 Known Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|-----------|
| Single SQLite instance | No distributed writes | Use `BUS_BACKEND=redis` for horizontal scale |
| In-memory event bus | Lost on restart | Redis backend + persistence |
| LLM latency | ~1-3s per response | Streaming for better UX |
| Web scraping rate limit | May hit anti-scraping | Mock connector for development |

---

## 14. Security Considerations

### 14.1 Authentication & Authorization

**Token-Based:**
- Session tokens stored in auth.db
- Token expiry: 5 minutes (configurable)
- Token validation on protected routes

**Optional Login:**
- `UI_REQUIRE_LOGIN` environment variable
- Can run without authentication (dev mode)
- Per-user thread isolation when authenticated

### 14.2 Sensitive Data Handling

**Secrets Management:**
- API keys stored in environment variables
- Masked in logs/config dumps
- Never committed to git (.gitignore)

**Data Privacy:**
- User queries stored in chat.db
- Can be cleared/archived
- No data transmission to external services (except configured LLM)

### 14.3 API Security

**CORS:**
- Localhost only in development
- Configurable origins in production
- Credentials mode enabled for auth

**Input Validation:**
- Request payload validation with Pydantic
- SQL injection prevention via parameterized queries
- Tool schema validation for LLM-called functions

---

## 15. Deployment & Operational Considerations

### 15.1 Environment Setup

**Required Environment Variables:**
```env
# Critical
OPENROUTER_API_KEY=sk-...    # For LLM
MCP_AUTH_SECRET=<32+ chars>  # For auth

# Optional (with defaults)
ENVIRONMENT=development      # or production
BUS_BACKEND=inproc          # or redis
SERVICE_PORT=8000
LOG_LEVEL=INFO
UI_REQUIRE_LOGIN=0          # Set to 1 to enable auth
```

**Database Initialization:**
```python
# Automatic on startup (FastAPI lifespan)
init_db()           # Creates auth.db
init_chat_db()      # Creates chat.db
```

### 15.2 Startup Sequence

1. **FastAPI app creation** (`backend/main.py`)
2. **CORS & Auth middleware** registration
3. **Router registration** (all endpoints)
4. **Lifespan context manager starts:**
   - `init_db()` - Auth database
   - `init_chat_db()` - Chat database
   - `cleanup_empty_threads()` - Database cleanup
   - `alert_api.start()` - Alert engine
   - `pricing_optimizer.start()` - Price optimizer
5. **Server listening** on configured port

### 15.3 Production Deployment

**Recommendations:**

1. **Use Redis for bus**: `BUS_BACKEND=redis`
2. **External LLM**: OpenRouter has free tier
3. **Database backup**: Regular SQLite backups
4. **Monitoring**: Prometheus + Grafana for metrics
5. **Logging**: Centralized logging service (ELK, Datadog)
6. **API Gateway**: Nginx or similar for reverse proxy
7. **SSL/TLS**: HTTPS for all endpoints

---

## 16. Common Workflows & Use Cases

### 16.1 Adding a New Tool for Chat Agent

**Steps:**

1. **Implement tool function** in `core/agents/user_interact/tools.py`:
```python
def my_new_tool(param1: str, param2: int) -> Dict[str, Any]:
    """Your tool description."""
    # Implementation
    return {"result": "..."}
```

2. **Register in TOOLS_MAP**:
```python
TOOLS_MAP = {
    "my_new_tool": my_new_tool,
    # ... others
}
```

3. **Add tool schema** in `core/agents/user_interact/tool_schemas.py`:
```python
{
    "type": "function",
    "function": {
        "name": "my_new_tool",
        "description": "What it does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer"}
            },
            "required": ["param1", "param2"]
        }
    }
}
```

4. **Register mapping** in `tool_schemas.py`:
```python
AGENT_TOOL_MAPPING["my_new_tool"] = "UserInteractionAgent"
```

5. **User can now invoke:**
> "Can you run my_new_tool with 'value' and 42?"

### 16.2 Creating a New Alert Rule

**File:** `core/agents/alert_service/rules.py`

```python
{
    "id": "low_margin_alert",
    "title": "Low Profit Margin",
    "condition": "margin < 5",
    "severity": "warning",
    "sinks": ["ui", "slack"]
}
```

Rules evaluated in real-time when events published.

### 16.3 Extending Data Collection

**To support new data source:**

1. Create connector in `core/agents/data_collector/connectors/my_source.py`
2. Implement data fetching logic
3. Register in connector factory
4. DataCollectorAgent will use it autonomously

---

## 17. Troubleshooting Guide

### 17.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "LLM unavailable" in logs | API key missing/invalid | Set OPENROUTER_API_KEY |
| Chat agent says "no tools available" | Tool schemas not registered | Check tool_schemas.py |
| Prices not updating | Price optimizer not started | Check FastAPI lifespan startup |
| Alerts not appearing | AlertEngine failed to start | Check database permissions |
| Agent "acting dumb" | Tools don't support query | Add new tool or enhance existing |

### 17.2 Debug Mode

**Enable verbose logging:**
```env
LOG_LEVEL=DEBUG
MCP_AUTH_LOG_LEVEL=DEBUG
```

**Enable traces:**
```python
from core.agents.agent_sdk.activity_log import should_trace
# Traces written to structured logs
```

---

## 18. Future Architecture Enhancements

### 18.1 Short-Term (0-3 months)

- [ ] Distributed agent deployment (multi-process/multi-machine)
- [ ] Redis backend for scalable event bus
- [ ] Comprehensive metrics dashboard
- [ ] Advanced alert routing (conditional sinks)

### 18.2 Medium-Term (3-6 months)

- [ ] ML model training pipeline for demand prediction
- [ ] A/B testing framework for pricing algorithms
- [ ] Advanced reporting and analytics
- [ ] Audit logging for regulatory compliance

### 18.3 Long-Term (6-12 months)

- [ ] Multi-tenant support
- [ ] Custom pricing algorithm builder (GUI)
- [ ] Real-time competitor intelligence
- [ ] Automated policy enforcement

---

## 19. Conclusion

The backend architecture is a **sophisticated, event-driven, multi-agent system** designed for autonomous decision-making in dynamic pricing. Key strengths:

✅ **Modular agents** - Each with clear responsibility  
✅ **LLM-powered** - Autonomous intelligent decisions  
✅ **Tool-calling system** - Extensible capabilities  
✅ **Real-time streaming** - SSE for live chat  
✅ **Event-driven** - Loosely coupled components  
✅ **Configurable** - Environment-based setup  
✅ **Scalable** - Ready for horizontal scaling  

The system successfully balances automation with user control, providing both autonomous agents and interactive chat for managing dynamic pricing workflows.

---

**End of Report**

*For questions about specific components, refer to the code comments and inline documentation in respective files.*
