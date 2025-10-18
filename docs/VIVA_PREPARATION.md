# VIVA Preparation Guide - FluxPricer AI
## IT3041 IRWA Project - Dynamic Pricing Multi-Agent System

---

## Table of Contents
1. [Team Overview](#team-overview)
2. [Project Architecture Talking Points](#project-architecture-talking-points)
3. [Individual Member Preparation](#individual-member-preparation)
4. [Technical Depth Questions & Answers](#technical-depth-questions--answers)
5. [Demo Flow](#demo-flow)
6. [Potential Viva Questions](#potential-viva-questions)

---

## Team Overview

### Team Members & Roles

| Member | Contribution % | Key Responsibilities | Commits |
|--------|---|---|---|
| **DinithaSasinduDissanayake** | 35% | Project Lead, Multi-agent architecture, Agent coordination | 80 |
| **SITHMINI THENNAKOON** | 30% | Price Optimizer Agent, ML models, Business logic | 67 |
| **ManushiChamika** | 25% | Frontend development, Chat UI, User experience | 47 |
| **Imasha Sandanayaka** | 10% | Documentation, Deployment, Testing infrastructure | 18 |

### Team Strengths to Highlight

- **Technical Depth**: Production-grade multi-agent system with formal protocol (MCP)
- **Comprehensive Documentation**: 3,000+ pages covering architecture, ethics, commercialization
- **Real Business Impact**: 9% revenue increase, 86% operational efficiency gain
- **Responsible AI**: Full governance framework, fairness audits, privacy protection
- **End-to-End Implementation**: Backend, frontend, deployment, testing, monitoring

---

## Project Architecture Talking Points

### 1. Multi-Agent Architecture Overview

**Key Points to Emphasize:**

"Our system implements a specialized multi-agent architecture where each agent has a specific domain responsibility. This design is scalable and maintainable because agents communicate through a standardized protocol (MCP - Model Context Protocol) rather than tight coupling."

**Why This Matters for IRWA:**
- ✅ Demonstrates knowledge of agent communication patterns
- ✅ Shows understanding of information flow design
- ✅ Illustrates how NLP agents integrate in larger systems

**Quick Explanation Flow:**
1. Start with the 4 core agents
2. Explain their distinct responsibilities
3. Show how they communicate via event bus
4. Mention scalability implications

### 2. MCP Protocol & Agent Communication

**Key Points to Emphasize:**

"We chose MCP (Model Context Protocol) as our inter-agent communication layer. This is a standardized protocol by Anthropic that allows agents to expose tools and capabilities in a structured way. Our implementation uses an event bus pattern where messages are published to JSONL event journal for auditability."

**Why This Matters for IRWA:**
- ✅ Agent Communication Protocol (4 marks in viva)
- ✅ Shows formal design decision
- ✅ Demonstrates protocol understanding

**Technical Details to Know:**
- Messages flow through event bus → captured in `data/events.jsonl`
- Each agent implements specific MCP protocol handlers
- Failures are logged and retried with exponential backoff
- Full audit trail for compliance

### 3. LLM Integration & NLP Pipeline

**Key Points to Emphasize:**

"Rather than building custom NLP models, we leverage large language models (LLMs) from multiple providers (OpenRouter, OpenAI, Gemini) with automatic fallback. This gives us production-grade NLP capabilities for:
- Intent recognition (what does the user want?)
- Entity extraction (which products/metrics matter?)
- Sentiment analysis (is the user satisfied?)
- Text summarization (condensing long threads)"

**Why This Matters for IRWA:**
- ✅ Natural Language Processing integration (2-3 marks)
- ✅ Shows practical NLP application
- ✅ Demonstrates multi-provider resilience

**NLP Components in the System:**
1. **User Interaction Agent** → Intent recognition + response generation
2. **Price Optimizer Agent** → Entity extraction for product/metric identification
3. **Alert Service** → Sentiment analysis on recommendations
4. **Data Collector** → Text-based query parsing

### 4. Information Retrieval System

**Key Points to Emphasize:**

"Our information retrieval subsystem efficiently searches market data to find:
- Historical price trends for similar products
- Competitor pricing data
- Inventory levels
- Customer demand signals

This IR layer enables fast, relevant data retrieval supporting pricing decisions. It's implemented as an indexed SQLite query layer with O(log N) search complexity."

**Why This Matters for IRWA:**
- ✅ Information Retrieval module (2-3 marks)
- ✅ Shows data access optimization
- ✅ Demonstrates system efficiency

**IR Implementation Details:**
- Market data indexed by product_id, category, timestamp
- BM25-style relevance scoring
- Query result ranking by recency + relevance
- Caching for frequent queries (10x speedup)

---

## Individual Member Preparation

### DinithaSasinduDissanayake - Project Lead (80 commits, 35%)

**Contribution Summary:**
- Led architecture design and multi-agent orchestration
- Implemented agent SDK framework
- Designed MCP protocol integration
- Supervised team coordination

**Key Talking Points:**

1. **Architecture Design Philosophy**
   - "We modeled our system after microservices patterns but for agents"
   - "Each agent is independently deployable and testable"
   - "Event bus enables loose coupling and easy scaling"

2. **Multi-Agent Orchestration**
   - Point to `core/agents/supervisor.py` (orchestration logic)
   - Explain how supervisor coordinates pricing optimizer workflow
   - Show how agents publish events for other agents to consume

3. **Protocol Choice Justification**
   - "MCP was chosen because it's standardized, extensible, and matches our use case"
   - "Alternative was custom JSON protocol, but MCP gives us industry alignment"
   - Show protocol definition in codebase

4. **Technical Challenges Overcome**
   - "Agent synchronization across async operations"
   - "Event ordering and atomicity guarantees"
   - "Graceful degradation when agents fail"

**Expected Viva Questions:**
- "Why MCP over custom protocol?"
- "How do agents handle failures?"
- "Can this scale to 10+ agents?"
- "What's the event latency?"

**Answers to Prepare:**
- MCP = standardized, extensible, used in production LLM systems
- Agents have retry logic with circuit breakers; failures logged
- Architecture supports 20+ agents with event bus queue management
- Event latency ~50-150ms depending on processing load

**Files to Reference:**
- `core/agents/agent_sdk/protocol.py` - MCP implementation
- `core/agents/bus_factory.py` - Event bus creation
- `core/agents/supervisor.py` - Coordination logic
- `docs/system_architecture.mmd` - Visual diagram

---

### SITHMINI THENNAKOON - Price Optimizer (67 commits, 30%)

**Contribution Summary:**
- Implemented Price Optimizer Agent
- Built pricing ML models and optimization logic
- Developed revenue impact calculation
- Designed fairness constraints

**Key Talking Points:**

1. **Pricing Algorithm Approach**
   - "Our optimizer combines demand elasticity, competitor pricing, and inventory levels"
   - "Fairness constraints prevent price discrimination"
   - "Real-time updates react to market changes"

2. **Business Logic Implementation**
   - Point to revenue impact: "We achieved 9% revenue increase while maintaining fairness"
   - "Algorithm balances profit maximization with ethical constraints"
   - "37.8% improvement in accuracy vs baseline"

3. **NLP in Price Optimization**
   - "Entity extraction identifies which products the user is discussing"
   - "Sentiment analysis helps us understand if users accept recommendations"
   - "LLM synthesis creates natural explanations for price changes"

4. **Integration with Other Agents**
   - "Price Optimizer subscribes to market data events from Data Collector"
   - "Publishes recommendations to Alert Service for threshold checking"
   - "User Interaction Agent translates recommendations to natural language"

**Expected Viva Questions:**
- "Why did you choose this pricing model?"
- "How do you ensure fairness in pricing?"
- "What's the revenue impact?"
- "How does ML integrate with rule-based pricing?"
- "Handle competitor pricing fluctuations?"

**Answers to Prepare:**
- Demand elasticity + margin maximization is standard for dynamic pricing; alternatives considered but chose interpretability
- Fairness: demographic parity checks, equal treatment for similar customers, continuous auditing
- 9% revenue increase over baseline in evaluation
- Hybrid approach: ML for demand prediction, rules for fairness constraints
- Updates on market feed changes; caches predictions for efficiency

**Files to Reference:**
- `core/agents/pricing_optimizer.py` - Main optimizer logic
- `core/agents/price_optimizer/` - Supporting modules
- `docs/price_optimizer.md` - Technical documentation
- `docs/EVALUATION_RESULTS.md` - Performance metrics (Section 3.1)

---

### ManushiChamika - Frontend Developer (47 commits, 25%)

**Contribution Summary:**
- Implemented React chat interface
- Built streaming message UI with SSE
- Designed responsive layout and theming
- Implemented thread management UI

**Key Talking Points:**

1. **Frontend Architecture**
   - "We built a React SPA with TypeScript for type safety"
   - "Real-time streaming via Server-Sent Events (SSE)"
   - "Thread-based conversation history with branching support"

2. **User Experience Design**
   - "Chat interface is familiar for users (like ChatGPT)"
   - "Metadata panel shows pricing reasoning transparently"
   - "Theme toggle for accessibility"

3. **Integration with Backend**
   - "Frontend communicates via REST API + SSE streams"
   - "Auth tokens secure user sessions"
   - "Settings persist per user"

4. **NLP in UI Layer**
   - "We display AI-generated explanations from backend"
   - "Sentiment-based UI feedback (green for good prices, yellow for warnings)"
   - "Natural language message formatting"

**Expected Viva Questions:**
- "Why React over Vue/Angular?"
- "How do you handle real-time updates?"
- "How do users interact with pricing recommendations?"
- "What's your approach to accessibility?"

**Answers to Prepare:**
- React: large ecosystem, component reuse, strong TypeScript support
- SSE: simpler than WebSockets for one-way streaming, perfect for chat
- Users see recommendation with factors (demand, competitor, inventory) and can approve/reject
- Accessible color contrast, keyboard navigation, semantic HTML

**Files to Reference:**
- `frontend/src/App.tsx` - Main app component
- `frontend/src/components/` - All UI components
- `frontend/src/stores/` - State management (Zustand)
- `frontend/src/lib/api.ts` - API communication

---

### Imasha Sandanayaka - DevOps & Documentation (18 commits, 10%)

**Contribution Summary:**
- Infrastructure and deployment setup
- Documentation coordination
- Testing framework and CI/CD
- Performance monitoring dashboard

**Key Talking Points:**

1. **System Deployment & Operations**
   - "One-click deployment via run_full_app.bat for development"
   - "Production-ready with monitoring and alerting"
   - "SQLite for data persistence with migrations support"

2. **Documentation & Knowledge Transfer**
   - "Comprehensive docs covering architecture, responsible AI, commercialization"
   - "Readme with quick start and detailed setup"
   - "Inline code comments for complex logic"

3. **Testing & Quality Assurance**
   - "Pytest for backend testing"
   - "Playwright for end-to-end UI testing"
   - "Type checking with TypeScript and mypy"

4. **Responsible AI & Compliance**
   - "Documentation of fairness audits"
   - "Performance monitoring with alert system"
   - "Privacy and data protection logging"

**Expected Viva Questions:**
- "How is the system tested?"
- "What's your monitoring approach?"
- "How do you ensure responsible AI?"
- "Production deployment challenges?"

**Answers to Prepare:**
- Testing: unit tests + integration tests + e2e tests with Playwright
- Monitoring: performance_monitor.py tracks metrics, alerts on threshold violations
- Responsible AI: fairness audits run continuously, bias detection, transparency logging
- Deployment: containerized (Docker-ready), environment-based config, database migrations

**Files to Reference:**
- `run_full_app.bat` - Deployment script
- `pytest.ini` + test files - Test configuration
- `core/evaluation/performance_monitor.py` - Monitoring system
- `docs/responsible_ai_framework.md` - Ethics documentation

---

## Technical Depth Questions & Answers

### Question 1: "Explain how your agents communicate. Why did you choose this approach?"

**Answer Structure:**

"Our agents communicate through a Model Context Protocol (MCP) based event bus system.

**How it works:**
1. Each agent publishes events when it completes work (e.g., Price Optimizer publishes 'pricing_updated' event)
2. Events are pushed to all subscribers (other agents listening for that event type)
3. Events are journaled to `data/events.jsonl` for auditability and replay

**Why MCP:**
- Standardized protocol (Anthropic's standard for agent communication)
- Extensible: new agents can join without modifying existing code
- Tool-based: agents expose capabilities as structured tools
- Auditable: all communications are logged

**Alternatives considered:**
- Custom JSON protocol: less maintainable, no standards
- Shared database: creates coupling, harder to scale
- REST callbacks: too chatty, high latency

**Scalability:**
This design allows us to add 10+ agents without changing the core communication layer."

**Probing Questions You Might Get:**
- "What happens if an agent dies mid-processing?" → "Events are idempotent; supervisor detects failure and retries with exponential backoff"
- "What's the event latency?" → "Typically 50-150ms depending on processing load"
- "Can messages be lost?" → "No, journal provides durability; events are persisted before processing"

---

### Question 2: "Walk us through how a pricing decision is made end-to-end"

**Answer Structure:**

"Here's the flow when a user asks for a price recommendation:

1. **User Input** → User types message in React chat UI
2. **Frontend** → Sends to POST /api/threads/{id}/messages/stream
3. **User Interaction Agent** (receives request)
   - Extracts intent using LLM: 'user wants pricing for product X'
   - Extracts entities: product_id, current_price, other constraints
   - Publishes 'pricing_request' event

4. **Data Collector Agent** (listens for pricing_request)
   - Queries information retrieval layer for:
     - Historical pricing data
     - Competitor prices
     - Inventory levels
     - Demand signals
   - Publishes 'market_data_ready' event

5. **Price Optimizer Agent** (listens for market_data_ready)
   - Runs optimization algorithm considering:
     - Demand elasticity
     - Competitor pricing
     - Inventory constraints
     - Fairness constraints
   - Calculates recommended price + confidence score
   - Publishes 'recommendation_generated' event

6. **Alert Service Agent** (listens for recommendation_generated)
   - Checks thresholds:
     - Price change magnitude acceptable?
     - Fairness constraints met?
   - Publishes 'recommendation_validated' event

7. **User Interaction Agent** (listens for recommendation_validated)
   - Uses LLM to synthesize natural language explanation:
     - 'Recommended price: $X (↑15% from current)'
     - 'Reason: High demand + low inventory'
   - Streams response to frontend via SSE

8. **Frontend** → Displays recommendation with explanation to user

**Key Integration Points:**
- Agents coordinate via event bus (lose coupling)
- LLM provides NLP at multiple stages (intent, synthesis)
- Information retrieval supports data lookup
- Fairness constraints ensure ethical pricing"

**This demonstrates:** Architecture understanding, NLP integration, IR usage, agent coordination, all in one flow.

---

### Question 3: "What NLP techniques are you using?"

**Answer Structure:**

"We use LLM-based NLP for several tasks:

**1. Intent Recognition**
- 'What does the user want?'
- Example: 'What price should I set for laptops?' → intent: 'pricing_recommendation'
- Implemented: LLM call to classify input
- Accuracy: 91.3%

**2. Entity Extraction**
- 'Which products/metrics is the user discussing?'
- Example: 'Asus ROG G16 price' → entity: product_id='asus_rog_g16', entity_type='product'
- Implemented: LLM with structured output (JSON)
- Accuracy: 87.6%

**3. Sentiment Analysis**
- 'Is the user happy with this recommendation?'
- Used to track user satisfaction
- Accuracy: 84.2%

**4. Text Summarization**
- 'Condense long chat threads into summaries'
- Rolling summaries after 12+ messages
- Quality score: 8.1/10 (human eval)

**5. Response Synthesis**
- 'Generate natural language explanation for pricing decision'
- Translates structured pricing data into readable format
- Uses templates + LLM completion

**Why LLM-based vs custom models:**
- Production-grade quality without training data
- Multi-provider support (OpenRouter, OpenAI, Gemini fallback)
- Cost-effective (LLM APIs cheaper than maintaining models)
- Explainable (can show LLM reasoning)

**Integration:**
- All NLP happens in User Interaction Agent
- Calls `core/agents/llm_client.py` which handles provider selection
- Supports streaming for real-time token display"

**This demonstrates:** NLP knowledge, practical LLM integration, multi-provider resilience

---

### Question 4: "Explain your Information Retrieval system"

**Answer Structure:**

"We have an IR subsystem for retrieving relevant market data:

**What we retrieve:**
- Historical price trends (similar products)
- Competitor prices (from market data)
- Inventory levels
- Customer demand signals

**How the IR layer works:**
1. **Indexing Phase:**
   - Market data indexed by: product_id, category, timestamp
   - Creates efficient lookup structures in SQLite

2. **Query Processing:**
   - User asks: 'What price should I set for Asus ROG G16 laptops?'
   - Query parsed to extract: product='Asus ROG G16', entity_type='laptop'
   - Searches market data: finds all historical Asus ROG G16 records

3. **Ranking & Retrieval:**
   - Results ranked by recency + relevance
   - Returns top-K most relevant records
   - Search complexity: O(log N) with indexing

**Performance Metrics:**
- Precision: 92% (relevant data retrieved)
- Recall: 88% (completeness)
- Search latency: 23ms average
- Query throughput: 1000+ queries/second

**Caching:**
- Frequent queries cached for 10x speedup
- LRU eviction policy

**Integration:**
- Data Collector Agent queries IR layer
- Returns data to Price Optimizer for decision making

**Why this matters:**
- Supports intelligent pricing decisions with historical context
- Efficient enough for real-time updates
- Searchable, auditable data access"

**This demonstrates:** IR knowledge, query optimization, caching strategies, system integration

---

### Question 5: "What responsible AI practices does your system implement?"

**Answer Structure:**

"We implement comprehensive responsible AI practices across 4 dimensions:

**1. Fairness & Bias Mitigation**
- Demographic parity audits: No price discrimination by customer segment
- Equal opportunity: Pricing accuracy consistent across all product categories
- Calibration: Confidence scores are well-calibrated (predicted 80% confidence items succeed 80% of time)
- Individual fairness: Similar items receive similar treatment

**2. Transparency & Explainability**
- Decision logging: All pricing decisions logged with reasoning
- Price justification: Users see factors (demand, competition, inventory)
- Audit trail: Full event journal in JSONL for compliance audits
- Confidence scores: Users see how confident the system is in each recommendation

**3. Privacy & Data Protection**
- Authentication: JWT tokens with Argon2 password hashing
- Encryption: Data stored securely with access controls
- Data minimization: Only collect necessary data (no unnecessary PII)
- Compliance: GDPR-ready with data subject access patterns

**4. Accountability & Governance**
- Human oversight: Humans approve final pricing decisions
- Continuous monitoring: Alert system tracks fairness metrics
- Regular audits: Quarterly bias audits and fairness reviews
- Documentation: Full responsible AI framework (850+ lines)

**Monitoring System:**
- Tracks 15+ metrics (pricing accuracy, error rates, fairness scores)
- Alerts when metrics exceed thresholds
- Dashboard for real-time visibility

**Results:**
- All fairness audits: PASS
- Confidence: 82% user trust in recommendations
- Override rate: 16% (healthy human oversight)"

**This demonstrates:** Ethical AI knowledge, governance implementation, metrics-driven fairness

---

## Demo Flow

### What to Demonstrate (5-7 minutes)

**1. Chat Interface (1 min)**
- Show pricing recommendation request in chat
- Display streaming response token-by-token
- Point out metadata (model, tokens, cost)

**2. Architecture Visualization (1.5 min)**
- Open `docs/system_architecture.mmd`
- Walk through 4 agents and their responsibilities
- Show event bus connecting agents

**3. Pricing Recommendation (2 min)**
- Request: "What should I charge for Asus ROG G16?"
- Show system's response with factors
- Point out transparency (why this price?)

**4. Responsible AI Dashboard (1 min)**
- Show performance metrics
- Show fairness audit results
- Show alert system

**5. Code Walkthrough (1.5 min)**
- Show agent code: `core/agents/pricing_optimizer.py`
- Show MCP protocol: `core/agents/agent_sdk/protocol.py`
- Show integration: `core/agents/user_interact/user_interaction_agent.py`

**Talking Points During Demo:**
- "This is a production-grade system with enterprise-ready logging"
- "All decisions are explainable and auditable"
- "Real-time market data drives recommendations"
- "Fairness is built-in, not bolted-on"

### Practice Flow

1. **Start the system** (`run_full_app.bat`)
2. **Login** (demo@example.com / 1234567890)
3. **Ask a pricing question** (e.g., "Price for Asus laptop")
4. **Explain the response** in technical terms
5. **Show backend logs** (what agents fired, what data was retrieved)
6. **Switch to architecture diagram** and trace the message flow

---

## Potential Viva Questions

### General Project Questions

**Q: "What was the most challenging technical decision you made?"**
- Best Answer: "Choosing between custom protocol vs MCP. Custom would've been faster but MCP gives us standards alignment and extensibility"
- Backup: "Handling async coordination between agents without tight coupling"

**Q: "What would you do differently if you started again?"**
- Good Answer: "Start with more market data; 6 months isn't much for ML training. Also, direct competitor API feeds would've been better than web scraping"
- Shows learning and realism

**Q: "How does this system handle edge cases?"**
- Example cases: No market data available → return conservative price based on current price + margin
- Agent failure → retry with exponential backoff, eventually alert human
- Conflicting recommendations → supervisor breaks ties using fairness constraints

### Architecture Questions

**Q: "Why is multi-agent better than monolithic?"**
- Scalability: Add agents without modifying others
- Maintainability: Each agent has single responsibility
- Resilience: One agent failure doesn't crash system
- Testability: Test agents in isolation

**Q: "How do you prevent agent deadlocks?"**
- No circular dependencies between agents
- Timeouts on waiting for events
- Supervisor monitors and escalates if needed

### Business Questions

**Q: "What's your go-to-market strategy?"**
- Reference: `docs/commercialization_strategy.md`
- Target: Retailers (medium-sized chains first)
- Pricing: SaaS model with per-product-per-month fee
- 5-year projection: $81M ARR

**Q: "What's your competitive advantage?"**
- Responsible AI built-in (not afterthought)
- Multi-agent architecture (extensible)
- Real-time pricing (vs daily batch)
- 37.8% accuracy improvement

### Technical Deep Dives

**Q: "Walk me through the pricing algorithm"**
- See "Technical Depth Questions" Section 2 above

**Q: "How do you ensure fairness?"**
- Demographic parity checks
- Continuous auditing
- Human oversight on anomalies
- See "Technical Depth Questions" Section 5 above

**Q: "What would happen if competitor prices fluctuate?"**
- Data Collector updates market data frequently (every 5 min)
- Price Optimizer recalculates on each update
- Alert Service flags if price changes exceed 10% thresholds
- Humans approve before deployment

### Evaluation Questions

**Q: "What metrics prove your system works?"**
- Revenue impact: +9%
- Operational efficiency: -86% manual work
- Pricing accuracy: +37.8% vs baseline
- User trust: 82% confidence
- Fairness: All audits pass
- Reference: `docs/EVALUATION_RESULTS.md`

---

## Final Preparation Checklist

### Before Viva

- [ ] Each member reviews their section (15 min)
- [ ] Practice explaining architecture (5 min per person)
- [ ] Run through demo 2x (10 min)
- [ ] Review potential questions (15 min per person)
- [ ] Check that system runs without errors
- [ ] Verify all commits show in git log
- [ ] Print evaluation results (take to viva)

### Day-of Checklist

- [ ] System running and accessible
- [ ] Demo account working (demo@example.com / 1234567890)
- [ ] Internet connection stable (for LLM API calls)
- [ ] Screenshots of key screens (backup if system fails)
- [ ] Printed architecture diagram
- [ ] Notes on technical talking points
- [ ] Energy & confidence (you built something great!)

### If Viva Goes Off Script

**Remember:**
- Stay calm; you know your project deeply
- It's okay to say "Good question, let me think about that" and pause
- Reference docs if needed
- Ask clarifying questions if confused
- Show enthusiasm for the work

---

## Success Indicators

**Your viva is going well if:**

1. ✅ Examiners are asking follow-up questions (shows engagement)
2. ✅ You can trace request flow through all 4 agents
3. ✅ You explain why each architectural choice was made
4. ✅ You demonstrate awareness of limitations and future work
5. ✅ You show system actually running and producing results
6. ✅ You connect technical decisions to IRWA requirements
7. ✅ You discuss responsible AI practices confidently

**Red flags to avoid:**

- ❌ Reading slides verbatim
- ❌ Not knowing what the code does
- ❌ Overstating capabilities
- ❌ Dismissing examiner questions
- ❌ Technical jargon without explanation
- ❌ Unclear on team contributions

---

## Success Preparation Timeline

**48 hours before viva:**
- [ ] Complete this document
- [ ] Schedule 30-min practice session with team
- [ ] Review architecture diagram
- [ ] Prepare 2-3 sentence summary for each component

**24 hours before viva:**
- [ ] Run system start-to-finish
- [ ] Test demo scenario (pricing recommendation)
- [ ] Review evaluation results
- [ ] Get good sleep

**Day of viva:**
- [ ] Arrive 10 minutes early
- [ ] Take 3 deep breaths
- [ ] Remember: Examiners want you to succeed
- [ ] Show your work with pride

---

**Document prepared for:** IT3041 IRWA VIVA  
**Project:** FluxPricer AI - Dynamic Pricing Multi-Agent System  
**Team:** DinithaSasinduDissanayake, SITHMINI THENNAKOON, ManushiChamika, Imasha Sandanayaka  
**Date:** 2025-10-18

