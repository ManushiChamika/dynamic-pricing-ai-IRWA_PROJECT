# Price Optimization Agent (POA) Demo Guide for Viva

## Overview
This guide shows how to demonstrate the multi-agent system with User Interaction Agent (UIA) and Price Optimization Agent (POA) integration.

## Demo Flow

### 1. Simple Queries (UIA Only)
These queries will be handled by UIA without invoking POA:

**Example Queries:**
- "What is the current price of ASUS-ProArt-5979Ultr?"
- "Show me the product catalog"  
- "List recent price proposals"
- "How many products do we have in inventory?"

**Expected Behavior:**
- UI shows standard "Thinking..." indicator
- UIA processes query directly using database tools
- No POA invocation

### 2. Complex Pricing Queries (UIA → POA)
These queries will trigger POA invocation:

**Example Queries:**
- "Optimize the price for ASUS-ProArt-5979Ultr using AI and competitor analysis"
- "Run a profit maximization strategy for ASUS-ROG-Strix-1635P" 
- "Use machine learning model to price ASUS-TUF-Gaming-4738 competitively"
- "Apply rule-based pricing algorithm to SKU-123 with market analysis"

**Expected Behavior:**
- UI shows "🤖 Price Optimization Agent working..." indicator (yellow/orange bubble)
- UIA detects complexity and calls `run_pricing_workflow` tool
- POA executes full AI-powered workflow:
  - Market data freshness check
  - AI algorithm selection (rule_based, ml_model, or profit_maximization)
  - Price calculation
  - Proposal generation

### 3. Available Products for Demo
Use these SKUs in your queries:
- `SKU-123`: Demo - $100.0 (cost: $90.0)
- `ASUS-ProArt-5979Ultr`: ASUS ProArt 5979Ultra - $64747.0 (cost: $51797.6)
- `ASUS-ROG-Strix-1635P`: ASUS ROG Strix 1635Pro - $88758.0 (cost: $71006.4)
- `ASUS-TUF-Gaming-4738`: ASUS TUF Gaming 4738 - $70989.0 (cost: $56791.2)

## Key Points to Highlight

### 1. Agent Coordination
- **UIA**: Handles simple queries, routes complex ones to POA
- **POA**: AI-powered pricing with algorithm selection
- **Seamless handoff**: No user intervention needed

### 2. UI Status Indicators
- Standard queries: Blue "Thinking..." bubble
- POA workflows: Yellow "Price Optimization Agent working..." bubble
- Clear visual distinction between agent activities

### 3. AI Algorithm Selection
POA uses AI to choose between:
- **rule_based**: Conservative competitive pricing (2% under market average)
- **ml_model**: Machine learning demand-aware pricing
- **profit_maximization**: Aggressive profit-focused pricing (10% markup)

### 4. Real Pricing Logic
- Reads current prices and costs from database
- Considers market data and competitor prices
- Generates actual price proposals with reasoning
- Respects business constraints (margins, min/max prices)

## Demo Script

### Step 1: Start Application
```bash
cd "C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT"
python -m streamlit run app/streamlit_app.py
```

### Step 2: Navigate to Chat
- Go to Dashboard → Chat section
- Start new conversation

### Step 3: Demonstrate Simple vs Complex

**Simple Query Example:**
```
What is the current price of ASUS-ProArt-5979Ultr?
```
*Show: Standard blue thinking bubble, quick response*

**Complex Query Example:**
```
Optimize the price for ASUS-ProArt-5979Ultr using AI to maximize profit while staying competitive
```
*Show: Yellow POA bubble, longer processing time, detailed AI reasoning*

### Step 4: Show Algorithm Variety

**Conservative Pricing:**
```
Price ASUS-TUF-Gaming-4738 conservatively to maintain market share
```

**Profit Maximization:**
```
Maximize profit margins for ASUS-ROG-Strix-1635P
```

**ML-Based Pricing:**
```
Use machine learning to price SKU-123 based on demand patterns
```

## Troubleshooting

### If POA doesn't trigger:
- Ensure keywords like "optimize", "AI", "algorithm", "strategy" are in query
- Try more explicit phrases like "run pricing workflow"

### If errors occur:
- Check that all required environment variables are set (.env file)
- Verify database files exist (app/data.db)
- Ensure OpenRouter/OpenAI API keys are configured

### Database Issues:
- Run database migration scripts if tables missing
- Check that sample data exists in product_catalog table

## Success Metrics for Demo
✅ UIA handles simple queries quickly
✅ POA indicator appears for complex queries  
✅ AI selects appropriate algorithms
✅ Real price calculations with reasoning
✅ Seamless multi-agent coordination
✅ Professional UI with clear status indicators