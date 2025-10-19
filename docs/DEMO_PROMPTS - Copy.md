# Bulletproof Demo Prompts

These prompts are designed to showcase the system's capabilities reliably and safely. Each prompt has been validated against the current codebase and demonstrates core functionality without relying on experimental features.

---

## 1. Product Catalog Discovery & Analysis

**Prompt:**
```
Show me all products in my catalog and identify which ones have pricing that might need attention based on profit margins.
```

**What it demonstrates:**
- Multi-tool orchestration (catalog retrieval + analysis)
- Autonomous reasoning about business metrics
- Natural language to structured data queries

**Why it's safe:**
- Uses stable `/api/catalog/products` endpoint (backend/routers/catalog.py:80)
- Data already exists in `app/data.db` (5+ laptop products confirmed)
- Read-only operation with no side effects
- No external dependencies or network calls

**Expected behavior:**
System retrieves products from catalog, calculates margin ratios (current_price - cost) / current_price, and highlights products with margins below typical thresholds (~30%).

---

## 2. Price Anomaly Alert Investigation

**Prompt:**
```
Check if there are any recent pricing incidents or alerts that need my attention, and explain the most critical one.
```

**What it demonstrates:**
- Proactive monitoring and alert surfacing
- AI-powered alert interpretation (LLM Alert Agent)
- Integration between event bus (PRICE_PROPOSAL topic) and UI layer

**Why it's safe:**
- Uses well-tested alert system (core/agents/alert_service/)
- Backend endpoint `/api/alerts` provides structured data (backend/routers/alerts.py)
- LLM integration has smoke tests (scripts/test_llm_alert_agent.py)
- Alert engine runs rule-based detection with throttling/deduplication safeguards
- Read-only investigation workflow

**Expected behavior:**
System fetches incidents from alert.db, identifies unresolved/high-severity alerts, and provides natural language explanation of what triggered the alert and recommended actions.

---

## 3. Product Freshness Audit

**Prompt:**
```
Which products in my catalog have stale market data (older than 60 minutes)? Start with showing me the count.
```

**What it demonstrates:**
- Data quality monitoring
- Temporal reasoning and staleness detection
- Tool-driven data investigation (check_data_freshness, get_stale_products)

**Why it's safe:**
- Uses existing MCP tools from data_collector (core/agents/data_collector/tools.py:93)
- Queries read-only market_ticks table in app/data.db
- No data modification or external calls
- Built-in staleness threshold validation

**Expected behavior:**
System uses `get_stale_products` tool to query market_ticks, calculates time since last update for each product, returns count and list of SKUs with stale data (last_update > 60 minutes ago).

---

## 4. Conversational Price Reasoning

**Prompt:**
```
For LAPTOP-002, explain what factors would influence whether I should raise or lower the price, and what data you'd need to make a recommendation.
```

**What it demonstrates:**
- Multi-agent reasoning (combines catalog data with pricing knowledge)
- Transparent AI decision-making process
- Safe exploratory analysis without taking action
- Understanding of business constraints (cost, margin, competition)

**Why it's safe:**
- Purely analytical - no price changes applied
- Uses catalog data already in database (LAPTOP-002: HP Pavilion 14, $749.99)
- LLM reasoning without tool execution (no side effects)
- Educational interaction showing system's knowledge boundaries

**Expected behavior:**
System retrieves LAPTOP-002 from catalog, discusses factors like cost ($X), current margin, competitive positioning, demand indicators, and explains it would need market_ticks data (competitor prices, demand_index) to make specific recommendations.

---

## 5. Thread Continuity & Context Management

**Prompt (multi-turn sequence):**
```
Turn 1: "Show me products with price above $1000"
Turn 2: "Now check which of those have the highest margins"  
Turn 3: "What would happen if I reduced the price of the highest-margin one by 10%?"
```

**What it demonstrates:**
- Thread-based conversation memory
- Anaphora resolution ("those" referring to previous results)
- Multi-step reasoning with preserved context
- Hypothetical scenario analysis

**Why it's safe:**
- All operations are read-only queries until Turn 3
- Turn 3 is hypothetical calculation only (no actual price updates)
- Uses stable chat thread persistence (data/chat.db via backend/main.py)
- No state changes in product catalog or market data
- Conversation context managed by user_interaction_agent (core/agents/user_interact/)

**Expected behavior:**
- Turn 1: Filters products where current_price > 1000 (returns 3-4 laptops)
- Turn 2: Calculates margin for filtered set, ranks by margin percentage
- Turn 3: Takes highest margin product, simulates 10% reduction, calculates new margin and explains impact

---

## Usage Instructions

### Prerequisites
1. App must be running via `run_full_app.bat`
2. Login with credentials: `demo@example.com` / `1234567890`
3. Create new chat thread or select existing one

### Best Practices
- Start with Prompt 1 or 2 to establish baseline understanding
- Use Prompt 5 to demonstrate conversational intelligence
- Combine prompts naturally: e.g., "Show me stale products (Prompt 3), then check if any have recent alerts (Prompt 2)"
- If unexpected behavior occurs, refresh and retry - all prompts are idempotent

### What to Avoid During Demo
- **Do NOT** use prompts that:
  - Require Chrome MCP tools (web scraping) - needs manual browser launch
  - Actually apply price changes without explicit confirmation
  - Depend on external API keys (if not configured in .env)
  - Reference features mentioned in docs/ but not confirmed in working code

### Recovery Paths
- If catalog appears empty: Check `app/data.db` exists and contains product_catalog data
- If alerts are empty: Run `python scripts/smoke_price_proposal_alerts.py` to generate test alerts
- If chat appears broken: Clear thread and start new conversation
- If LLM errors occur: System falls back gracefully with non-LLM response

---

## Technical Validation

Each prompt validated against:
- ✅ Existing API endpoints (backend/routers/)
- ✅ Populated database tables (app/data.db)
- ✅ Tested agent tools (core/agents/*/tools.py)
- ✅ Smoke test coverage (scripts/smoke_*.py)
- ✅ Frontend integration (confirmed in hooks/components)

## Expected Demo Flow (5-7 minutes)

1. **Introduction (30s)**: Login, show landing page, navigate to chat
2. **Prompt 1 (60s)**: Catalog discovery - establishes data exists
3. **Prompt 2 (90s)**: Alert investigation - shows AI reasoning
4. **Prompt 5 (120s)**: Multi-turn conversation - shows context memory
5. **Prompt 4 (60s)**: Explanatory reasoning - shows transparency
6. **Q&A (60s)**: Handle audience questions with Prompt 3 or variations

---

## Troubleshooting

### "Product catalog is empty"
**Solution:** Run `python scripts/populate_sri_lanka_laptop_store.py` to repopulate data

### "No alerts found"
**Solution:** Run `python scripts/smoke_price_proposal_alerts.py` to generate test alerts

### "LLM not responding"
**Solution:** Check `.env` has valid API keys (OPENROUTER_API_KEY or OPENAI_API_KEY)

### "Chat thread not saving"
**Solution:** Ensure `data/chat.db` exists and has write permissions

---

## Advanced Variations (Optional)

Once core prompts work reliably, try these variations:

- **Batch Analysis**: "Show me all products with margin below 25% AND price above $1000"
- **Temporal Query**: "Have there been any price proposals for LAPTOP-003 in the last 24 hours?"
- **Comparative**: "Compare the margins of LAPTOP-001 and LAPTOP-004"
- **Counterfactual**: "If I increased costs by 5% across all products, which would fall below minimum margin?"

These demonstrate the same safe patterns (read-only analysis, hypothetical reasoning) with increased complexity.
