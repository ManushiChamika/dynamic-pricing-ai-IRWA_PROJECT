# Test Prompts for Dynamic Pricing AI System

## 🎯 Purpose
These are verified test prompts to demonstrate the multi-agent dynamic pricing system functionality after fixing the LLM boolean syntax error.

---

## 🤖 Simple UIA-Only Prompts
*Tests basic User Interaction Agent functionality with direct database queries*

### Database Queries
```
What brands do we have available?
```
```
How many products are in our catalog?
```
```
Show me all gaming laptops under 200,000 LKR
```
```
What is the most expensive laptop in our database?
```
```
Show me Dell laptops only
```

**Expected:** Quick responses with filtered product data, no complex agent workflows

---

## 🧠 Complex POA-Triggering Prompts
*Tests handoff from UIA to Pricing Optimization Agent*

### AI Pricing Optimization
```
Optimize pricing strategy for gaming laptops using AI algorithms
```
```
Maximize profit margins for HP laptops using advanced pricing algorithms
```
```
Use AI to set optimal prices for laptops considering market competition
```
```
Strategic pricing optimization for maximum revenue using machine learning
```
```
Optimize all laptop prices for competitive advantage and profit maximization
```

**Expected:** Multi-stage POA workflow with visible UI feedback and `price.proposal` events

---

## 🚨 Alert Agent Scenarios
*Tests Alert & Notification Agent integration*

### Critical Situation Detection
```
Check for any critical pricing situations that need immediate attention
```
```
Alert me if any products have pricing issues or competitive threats
```
```
Scan for pricing anomalies and margin breaches across all products
```

**Expected:** Alert scanning with severity levels and comprehensive monitoring

---

## 📊 Data Collection Scenarios
*Tests Data Collection Agent functionality*

### Market Intelligence
```
Collect latest market data from competitor websites for all laptops
```
```
Gather pricing intelligence from Daraz, Kapruka and other Sri Lankan sites
```
```
Update our market database with fresh competitor pricing data
```

**Expected:** Multi-source data collection with progress tracking and database updates

---

## 🔄 Multi-Agent Coordination
*Tests complex workflows involving multiple agents*

### Full System Demonstration
```
Collect fresh market data, optimize pricing strategy, and check for critical alerts
```
```
Update market intelligence and then optimize all laptop prices for maximum profit
```
```
Run comprehensive pricing analysis: gather data, optimize with AI, monitor risks
```
```
Perform end-to-end pricing optimization using all available agents
```

**Expected:** Sequential agent execution with visible handoffs (DCA → POA → ANA)

---

## 🎬 Recommended Demo Sequence

### Phase 1: Basic Functionality (2 minutes)
1. **Simple Query:** "What brands do we have available?"
2. **Verify:** Quick response with brand list

### Phase 2: Agent Handoff (3 minutes)
1. **Complex Query:** "Optimize pricing strategy for gaming laptops using AI algorithms"
2. **Monitor:** Activity tab for POA workflow stages
3. **Verify:** Multi-stage processing with real-time feedback

### Phase 3: Alert System (2 minutes)
1. **Alert Query:** "Check for any critical pricing situations that need immediate attention"
2. **Verify:** Alert scanning with severity classifications

### Phase 4: Data Collection (2 minutes)
1. **Collection Query:** "Collect latest market data from competitor websites for all laptops"
2. **Monitor:** Progress tracking in Activity view

### Phase 5: Full Coordination (3 minutes)
1. **Multi-Agent Query:** "Collect fresh market data, optimize pricing strategy, and check for critical alerts"
2. **Verify:** All four agents working in sequence
3. **Monitor:** Complete workflow in Activity view

**Total Demo Time: ~12 minutes**

---

## ✅ Success Indicators

### LLM Functionality Working:
- ❌ **Before Fix:** "[non-LLM assistant] LLM is not available. Please ensure the LLM client is configured properly."
- ✅ **After Fix:** Actual AI responses with reasoning and tool usage

### Agent Detection:
- Chat bubbles show agent-specific processing stages
- Activity view displays real-time agent operations
- Clear handoffs between UIA → POA/DCA/ANA

### Tool Integration:
- `execute_sql` - Database queries
- `run_pricing_workflow` - POA integration
- `collect_market_data` - DCA integration
- `scan_for_alerts` - ANA integration

---

## 🐛 Fixed Issue Summary

**Problem:** Python syntax error in `user_interaction_agent.py:288`
```python
# BROKEN (JavaScript boolean)
"force_refresh": {"type": "boolean", "default": false}

# FIXED (Python boolean)
"force_refresh": {"type": "boolean", "default": False}
```

**Impact:** 
- LLM client was available but tool definitions failed to parse
- Silent exception caused fallback to non-LLM responses
- All chat requests returned fallback message instead of AI responses

**Resolution:**
- Changed `false` to `False` in JSON schema definition
- LLM now processes requests correctly with full tool integration
- Multi-agent system fully operational

---

## 📝 Technical Notes

### System Configuration:
- **Database:** 20 Sri Lankan laptop products (LKR 50K-780K range)
- **LLM Providers:** OpenRouter (Grok) + Gemini fallback
- **Port:** Streamlit runs on 8501
- **Event System:** Price proposal events working correctly

### Agent Capabilities Verified:
- **UIA:** 9 specialized tools with proper handoff logic
- **POA:** Async workflow with AI algorithm selection
- **DCA:** Mock scraping with progress feedback
- **ANA:** Multi-type alert detection with severity levels

---

*File created: December 2024*
*Status: ✅ All prompts verified working after boolean syntax fix*