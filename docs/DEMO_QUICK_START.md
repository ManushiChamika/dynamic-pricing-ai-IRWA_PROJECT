# Demo Quick Start Guide

**Goal:** Showcase the Dynamic Pricing AI system in 5-7 minutes

## Pre-Demo Checklist

- [ ] Run `run_full_app.bat` 
- [ ] Login: `demo@example.com` / `1234567890`
- [ ] Verify products exist: Navigate to Pricing page OR use chat to ask "Show me all products"
- [ ] Have `docs/DEMO_PROMPTS.md` open for reference

## The 5 Bulletproof Prompts

### 1️⃣ Catalog Discovery (60s)
```
Show me all products in my catalog and identify which ones have pricing that might need attention based on profit margins.
```
**Shows:** Multi-tool orchestration, autonomous analysis

### 2️⃣ Alert Investigation (90s)  
```
Check if there are any recent pricing incidents or alerts that need my attention, and explain the most critical one.
```
**Shows:** Proactive monitoring, LLM-powered alert interpretation

### 3️⃣ Data Quality (60s)
```
Which products in my catalog have stale market data (older than 60 minutes)? Start with showing me the count.
```
**Shows:** Data freshness monitoring, temporal reasoning

### 4️⃣ Price Reasoning (60s)
```
For LAPTOP-002, explain what factors would influence whether I should raise or lower the price, and what data you'd need to make a recommendation.
```
**Shows:** Transparent AI reasoning, business understanding

### 5️⃣ Multi-Turn Context (120s)
```
Turn 1: Show me products with price above $1000
Turn 2: Now check which of those have the highest margins
Turn 3: What would happen if I reduced the price of the highest-margin one by 10%?
```
**Shows:** Context memory, anaphora resolution, hypothetical analysis

## Recommended Flow

1. **Start with #1** - Establishes data exists and system works
2. **Follow with #5** - Most impressive demo of conversational AI
3. **End with #2** - Shows practical business value
4. **Use #4 for Q&A** - Demonstrates transparency and safety

## Emergency Recovery

- **No products?** Run `python scripts/populate_sri_lanka_laptop_store.py`
- **No alerts?** Run `python scripts/smoke_price_proposal_alerts.py`  
- **LLM errors?** Check `.env` has API keys configured
- **Chat broken?** Refresh page and start new thread

## Key Talking Points

- ✅ **Safe by design:** All prompts are read-only or hypothetical
- ✅ **Multi-agent:** Uses specialized agents (catalog, pricing, alerts)
- ✅ **Event-driven:** Async communication via event bus
- ✅ **Transparent:** System explains its reasoning
- ✅ **Production-ready:** Authenticated, per-user data, tested endpoints

## What NOT to Demo

- ❌ Chrome web scraping (requires manual browser launch)
- ❌ Experimental features from docs that aren't fully implemented
- ❌ Actual price changes (unless explicitly requested and confirmed)
- ❌ External integrations without verified API keys

---

**Full details:** See `docs/DEMO_PROMPTS.md`
