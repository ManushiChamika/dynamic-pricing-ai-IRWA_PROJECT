# Dynamic Pricing AI - Viva Demo Guide

## Multi-Agent System Demo

### System Architecture
- **User Interaction Agent (UIA)**: Handles chat interface and simple queries
- **Price Optimization Agent (POA)**: Advanced AI-powered pricing analysis and optimization
- **Data Collection Agent**: Market data gathering (background)
- **Alert & Notification Agent**: Price change alerts (background)

---

## Demo Scenarios

### 1. Simple Queries (UIA handles alone)
These prompts show UIA working independently without POA:

**Prompt 1:** `Show me all laptops in our inventory`
- **Expected:** UIA uses `list_inventory` tool directly
- **UI Status:** Normal blue thinking bubble
- **Result:** Lists products from catalog

**Prompt 2:** `What is the current price of LAPTOP001?`
- **Expected:** UIA uses `execute_sql` or inventory lookup
- **UI Status:** Normal blue thinking bubble  
- **Result:** Returns specific price information

**Prompt 3:** `How many products do we have in stock?`
- **Expected:** UIA uses `execute_sql` for COUNT query
- **UI Status:** Normal blue thinking bubble
- **Result:** Returns inventory count

---

### 2. Complex Pricing Requests (UIA calls POA)
These prompts trigger the Price Optimization Agent:

**Prompt 4:** `Optimize pricing strategy for LAPTOP001 to maximize profit`
- **Expected:** UIA calls POA via `run_pricing_workflow`
- **UI Status:** Multi-stage POA progress indicators:
  - 🤖 Price Optimization Agent: Analyzing request...
  - 🧠 AI Brain: Selecting optimal algorithm...
  - 📊 Market Analysis: Processing competitive data...
  - ⚡ Executing pricing optimization...
- **POA Tasks:**
  - Analyzes user intent ("maximize profit")
  - AI selects `profit_maximization` algorithm
  - Processes market data and competitor prices
  - Calculates optimized price with detailed reasoning
- **Result:** Comprehensive pricing analysis with algorithm justification

**Prompt 5:** `I need competitive pricing analysis for gaming laptops`
- **Expected:** UIA calls POA for strategic analysis
- **UI Status:** POA multi-stage indicators
- **POA Tasks:**
  - AI brain selects appropriate algorithm (likely `rule_based` for competitive positioning)
  - Analyzes gaming laptop market segment
  - Processes competitor pricing data
  - Provides market-competitive recommendations
- **Result:** Strategic pricing recommendations with market analysis

**Prompt 6:** `Use AI to optimize pricing for LAPTOP005 based on market conditions`
- **Expected:** UIA calls POA for AI-driven optimization
- **UI Status:** POA multi-stage indicators
- **POA Tasks:**
  - AI selects `ml_model` algorithm for sophisticated analysis
  - Analyzes market volatility and trends
  - Considers price positioning relative to competitors
  - Calculates ML-inspired optimized price
- **Result:** Advanced AI pricing recommendation with market insights

---

## Key Demo Points to Highlight

### 1. Agent Coordination
- **UIA Intelligence**: UIA correctly decides when to handle queries alone vs when to call POA
- **System Prompt**: Enhanced instructions guide tool selection
- **POA Integration**: Seamless handoff to POA for complex pricing tasks

### 2. Price Optimization Agent Capabilities
- **AI Algorithm Selection**: LLM brain chooses optimal pricing strategy
- **Real Market Data**: Uses actual competitor pricing from database
- **Meaningful Analysis**: Algorithms provide realistic business logic:
  - `rule_based`: Conservative competitive pricing (-2% from market average)
  - `ml_model`: Advanced analysis with volatility and trend consideration
  - `profit_maximization`: Strategic premium positioning (+10-15% markup)

### 3. UI Experience
- **Visual Feedback**: Different colored progress indicators for different agents
- **Multi-Stage Progress**: Shows POA workflow steps (Analysis → AI Selection → Market Analysis → Execution)
- **Real-Time Updates**: Live status updates during POA execution

### 4. Business Value
- **Intelligent Routing**: Simple queries get fast responses, complex needs get sophisticated analysis
- **AI-Powered Strategy**: Real AI decision-making for algorithm selection
- **Market-Driven Pricing**: Uses actual competitive data for informed decisions
- **Scalable Architecture**: Clean separation of concerns between agents

---

## Technical Implementation Highlights

### Enhanced UIA System Prompt
```
- Use run_pricing_workflow for COMPLEX pricing requests that need advanced AI analysis, 
  market research, algorithm selection, or strategic pricing decisions
- Examples: 'optimize pricing strategy', 'maximize profit', 'competitive pricing analysis', 'AI-driven pricing'
```

### POA Algorithm Selection
```python
# AI-powered tool selection based on user intent and market context
def decide_tool(self, user_intent: str, available_tools: dict, market_context: dict = None):
    # Uses LLM to analyze intent and select optimal pricing algorithm
    # Considers market conditions, business objectives, and user goals
```

### UI Status Display
```python
# Multi-stage POA progress visualization
if requires_poa:
    # Stage 1: Analyzing request
    # Stage 2: AI algorithm selection  
    # Stage 3: Market analysis
    # Stage 4: Executing optimization
```

---

## Demo Flow Recommendation

1. **Start with Simple Query** (Prompt 1 or 2) - Show UIA working alone
2. **Show Complex Query** (Prompt 4) - Demonstrate POA integration and detailed analysis
3. **Highlight AI Decision Making** - Point out how the AI brain selected the algorithm
4. **Show Market Analysis** - Explain how real competitor data influenced the pricing
5. **Compare Results** - Show difference between simple lookup vs sophisticated analysis

This demonstrates a working multi-agent system where:
- **Simple queries** get handled efficiently by UIA
- **Complex pricing decisions** leverage AI-powered POA with real market analysis
- **UI provides clear feedback** about which agent is working
- **Business value** is delivered through intelligent routing and sophisticated analysis