# VIVA Demo Prompts - Multi-Agent Dynamic Pricing System

## 🎯 Demo Strategy

**Goal**: Show clear differentiation between agents and their coordination
**Interface**: Chat interface with Activity view for real-time agent operations
**Data**: 20 Sri Lankan laptop products (LKR 50,855 - LKR 780,223)

---

## 🤖 Agent Demonstrations

### 1. User Interaction Agent (UIA) - Simple Queries
*Shows direct database access without optimization*

**Demo Prompts:**
```
What laptops do we have under LKR 100,000?
```
```
Show me all ASUS laptops in our inventory
```
```
What's the most expensive laptop we have?
```

**Expected Behavior:**
- ✅ Direct SQL queries to database
- ✅ Quick responses with product lists
- ✅ Basic filtering and search
- ❌ No complex pricing analysis

---

### 2. Price Optimization Agent (POA) - Complex Workflows
*Shows AI-driven pricing optimization with multi-stage processing*

**Demo Prompts:**
```
I need to optimize pricing for our budget laptop category to maximize revenue while staying competitive
```
```
Analyze and suggest price adjustments for laptops that haven't sold well in the competitive market
```
```
Create a pricing strategy for our premium gaming laptops considering market positioning
```

**Expected Behavior:**
- ✅ UIA detects complexity and calls POA
- ✅ Multi-stage workflow visible in chat:
  - 🔵 Data Analysis
  - 🟡 Market Research  
  - 🟠 Strategy Development
  - 🟢 Recommendation Generation
- ✅ `price.proposal` events appear in Activity view
- ✅ Detailed analysis with reasoning

---

### 3. Alert & Notification Agent - Critical Situations
*Shows proactive monitoring and alerts*

**Demo Scenarios:**
```
What would happen if our competitor drops their laptop prices by 30%?
```
```
Alert me if any product pricing becomes uncompetitive
```

**Expected Behavior:**
- ✅ Critical situation detection
- ✅ Alert notifications in Activity view
- ✅ Automated response suggestions

---

### 4. Data Collection Agent - Market Intelligence
*Shows external data gathering with UI feedback*

**Demo Prompts:**
```
Collect current market prices for similar laptops from competitors
```
```
Update our market intelligence database with latest pricing trends
```

**Expected Behavior:**
- ✅ Data collection progress in Activity view
- ✅ Status updates during collection
- ✅ Database updates confirmation

---

## 📊 Activity View Monitoring

**Operations → Activity** shows real-time agent coordination:
- `price.proposal` - POA optimization results
- `alert.critical` - Alert agent notifications  
- `data.collected` - Data collector updates
- `agent.coordination` - Inter-agent communication

---

## 🎬 Demo Sequence for Viva

### Part 1: Simple vs Complex (5 minutes)
1. **UIA Simple**: "What laptops do we have under LKR 100,000?"
2. **POA Complex**: "Optimize pricing for budget laptops to maximize revenue"
3. **Show Activity View**: Point out POA workflow stages and events

### Part 2: Multi-Agent Coordination (3 minutes)
1. **Alert Scenario**: "What if competitor drops prices by 30%?"
2. **Data Collection**: "Update market intelligence for pricing"
3. **Show Activity View**: Real-time agent activities

### Part 3: Business Value (2 minutes)
1. Explain how each agent serves different business needs
2. Show pricing recommendations and their rationale
3. Demonstrate scalability through agent coordination

---

## 🛠️ Technical Highlights

- **UIA**: 7 specialized tools (SQL, pricing workflows, memory management)
- **POA**: Async workflow engine with event publishing
- **Activity System**: Event-driven architecture with real-time UI updates
- **Integration**: Seamless handoff between agents based on query complexity

---

## 📝 Key Messages for Evaluators

1. **Agent Specialization**: Each agent has distinct capabilities and use cases
2. **Intelligent Routing**: UIA determines when to involve other agents
3. **Real-time Visibility**: All agent activities visible through Activity view
4. **Business Ready**: Realistic pricing scenarios with Sri Lankan market data
5. **Scalable Architecture**: Event-driven design supports easy agent addition

---

## ⚡ Quick Start Commands

```bash
# Start the application
streamlit run app/streamlit_app.py

# Verify data (should show 20 products)
python verify_data.py

# Test imports
python -c "from core.agents.user_interact.user_interaction_agent import UserInteractionAgent; print('✅ UIA loaded')"
```

---

**💡 Pro Tip**: Keep Activity view open during demo to show real-time agent coordination!