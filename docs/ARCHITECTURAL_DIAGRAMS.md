# Architectural Diagrams

This document contains Mermaid diagrams visualizing the system architecture.

## Table of Contents
1. [Event-Driven Agent Communication Flow](#event-driven-agent-communication-flow)
2. [LLM Tool Orchestration Workflow](#llm-tool-orchestration-workflow)
3. [SSE Streaming Architecture](#sse-streaming-architecture)
4. [Market Data Collection Flow](#market-data-collection-flow)
5. [Governance & Price Application](#governance--price-application)
6. [MCP Dual-Mode Architecture](#mcp-dual-mode-architecture)
7. [Component Interaction Overview](#component-interaction-overview)

---

## Event-Driven Agent Communication Flow

```mermaid
graph TD
    A[External Trigger] --> B[Supervisor Agent]
    B -->|OPTIMIZATION_REQUEST| C[Pricing Optimizer Agent]
    B -->|MARKET_FETCH_REQUEST| D[Data Collector Agent]
    
    D -->|MARKET_FETCH_ACK| B
    D -->|MARKET_TICK| E[Event Bus]
    D -->|MARKET_FETCH_DONE| B
    
    E -->|MARKET_TICK| F[Alert Engine]
    E -->|MARKET_TICK| C
    
    C -->|PRICE_PROPOSAL| G[Auto Applier]
    C -->|PRICE_PROPOSAL| H[Governance Execution Agent]
    C -->|PRICE_PROPOSAL| F
    
    G -->|PRICE_UPDATE| I[Event Journal]
    H -->|PRICE_UPDATE| I
    
    F -->|ALERT| J[Notification Services]
    
    I -->|Append| K[events.jsonl]
    
    style E fill:#e1f5ff
    style I fill:#fff4e1
    style K fill:#f0f0f0
```

**Key Points**:
- All agents communicate through centralized Event Bus
- Event Journal logs every event to `events.jsonl` for audit trail
- Pub-sub pattern allows loose coupling between agents

---

## LLM Tool Orchestration Workflow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant LLMClient
    participant OpenRouter
    participant OpenAI
    participant Gemini
    participant ToolRegistry
    participant Agent
    
    User->>API: Send message
    API->>LLMClient: chat_with_tools_stream()
    
    LLMClient->>OpenRouter: Try provider 1
    
    alt OpenRouter Success
        OpenRouter-->>LLMClient: Tool call request
        LLMClient->>ToolRegistry: execute_tool()
        ToolRegistry->>Agent: call tool function
        Agent-->>ToolRegistry: result
        ToolRegistry-->>LLMClient: serialized result
        LLMClient->>OpenRouter: Continue with result
        OpenRouter-->>LLMClient: Final response
    else OpenRouter Fails
        OpenRouter-->>LLMClient: Error
        LLMClient->>OpenAI: Try provider 2
        
        alt OpenAI Fails
            OpenAI-->>LLMClient: Error
            LLMClient->>Gemini: Try provider 3
        end
    end
    
    LLMClient-->>API: Stream text + tool events
    API-->>User: SSE events
```

**Key Points**:
- Multi-provider failover with automatic retry
- Tool execution happens synchronously within streaming
- Up to `max_rounds` iterations for complex workflows
- Tracks token usage and costs per request

---

## SSE Streaming Architecture

```mermaid
sequenceDiagram
    participant User
    participant React
    participant messageStore
    participant sseClient
    participant Backend
    participant LLMClient
    participant Agent
    
    User->>React: Send message
    React->>messageStore: send(text)
    
    alt Draft Thread
        messageStore->>Backend: POST /threads (create)
        Backend-->>messageStore: {thread_id: 123}
        messageStore->>messageStore: Update URL
    end
    
    messageStore->>sseClient: streamMessage()
    sseClient->>Backend: POST /threads/{id}/messages/stream
    
    Backend->>LLMClient: Process message
    
    Backend-->>sseClient: event: thinking\ndata: {}
    sseClient->>messageStore: onUpdate({type: "thinking"})
    messageStore->>React: Show "Thinking..."
    
    Backend->>Agent: Execute workflow
    Backend-->>sseClient: event: agent\ndata: {"name": "PriceOptimizer"}
    sseClient->>messageStore: onUpdate({type: "agent"})
    messageStore->>React: Show agent badge
    
    loop For each tool
        LLMClient->>Agent: Call tool
        Backend-->>sseClient: event: tool_call\ndata: {name, status: "start"}
        sseClient->>messageStore: onUpdate({type: "tool_call"})
        messageStore->>React: Show tool indicator
        
        Agent-->>LLMClient: Result
        Backend-->>sseClient: event: tool_call\ndata: {name, status: "end"}
        sseClient->>messageStore: onUpdate({type: "tool_call"})
    end
    
    loop For each text chunk
        LLMClient-->>Backend: Text delta
        Backend-->>sseClient: event: message\ndata: {"delta": "..."}
        sseClient->>messageStore: onUpdate({type: "message"})
        messageStore->>React: Append to live message
    end
    
    Backend-->>sseClient: event: message\ndata: {id, tokens, cost}
    sseClient->>messageStore: onUpdate({type: "message"})
    messageStore->>React: Show final message
    
    Backend-->>sseClient: event: done\ndata: {}
    sseClient->>messageStore: onUpdate({type: "done"})
    messageStore->>React: Cleanup streaming state
```

**Key Points**:
- Single SSE connection carries multiple event types
- Frontend updates UI in real-time as events arrive
- Watchdog timer (25s) prevents hanging connections
- Draft threads auto-created on first message

---

## Market Data Collection Flow

```mermaid
sequenceDiagram
    participant Client
    participant EventBus
    participant DataCollector
    participant WebScraper
    participant MockConnector
    participant Database
    
    Client->>EventBus: Publish MARKET_FETCH_REQUEST
    Note over EventBus: {request_id, sku, sources, urls}
    
    EventBus->>DataCollector: Notify subscriber
    DataCollector->>DataCollector: Check duplicate
    
    alt Duplicate Request
        DataCollector-->>DataCollector: Log & ignore
    else New Request
        DataCollector->>Database: Insert job (QUEUED)
        DataCollector->>EventBus: Publish MARKET_FETCH_ACK
        Note over EventBus: {job_id, status: "RUNNING"}
        
        DataCollector->>Database: Update job (RUNNING)
        
        par Parallel Scraping
            DataCollector->>WebScraper: fetch(url)
            DataCollector->>MockConnector: fetch(sku)
        end
        
        WebScraper-->>DataCollector: {status, price}
        MockConnector-->>DataCollector: {status, price}
        
        loop For each result
            DataCollector->>Database: Insert market_tick
            DataCollector->>EventBus: Publish MARKET_TICK
            Note over EventBus: {sku, price, source}
        end
        
        DataCollector->>Database: Update job (DONE)
        DataCollector->>EventBus: Publish MARKET_FETCH_DONE
        Note over EventBus: {job_id, tick_count}
    end
    
    EventBus->>Client: Notify subscriber
```

**Key Points**:
- 3-event workflow: REQUEST → ACK → DONE
- Job tracking in database enables monitoring
- Supports multiple connectors (web scraper, mock, API)
- Duplicate prevention via instance-level set

---

## Governance & Price Application

```mermaid
flowchart TD
    A[PRICE_PROPOSAL Event] --> B{Auto Apply<br/>Enabled?}
    
    B -->|Yes| C[Auto Applier]
    B -->|No| D[Governance Execution Agent]
    
    C --> E{Check<br/>Guardrails}
    D --> E
    
    E -->|Margin < min_margin| F[Log Decision: REJECTED]
    E -->|Delta > max_delta| F
    E -->|Pass| G{Optimistic<br/>Concurrency<br/>Check}
    
    G -->|Base price changed| H[Log Decision: STALE]
    G -->|Success| I[Update pricing_list]
    G -->|Lock contention| J[Retry with<br/>Exponential Backoff]
    
    J --> G
    
    I --> K[Log Decision: APPLIED_AUTO]
    K --> L[Publish PRICE_UPDATE]
    
    F --> M[Do not apply]
    H --> M
    
    style E fill:#fff4e1
    style G fill:#e1f5ff
    style K fill:#e1ffe1
    style F fill:#ffe1e1
    style H fill:#ffe1e1
```

**Key Points**:
- Dual-path governance: AutoApplier (fast) vs GovernanceExecutionAgent (enhanced)
- Guardrails: `min_margin`, `max_delta`, `auto_apply` toggle
- Optimistic concurrency prevents race conditions
- All decisions logged to immutable audit trail

---

## MCP Dual-Mode Architecture

```mermaid
graph TD
    A[Agent Code] --> B{Read<br/>USE_MCP<br/>from .env}
    
    B -->|true| C[MCP Client Mode]
    B -->|false| D[Local Function Mode]
    
    C --> E[get_price_optimizer_client]
    D --> E
    
    E -->|USE_MCP=true| F[MCPClient Instance]
    E -->|USE_MCP=false| G[Local Function Facade]
    
    F --> H[Connection Pool]
    H --> I[MCP Server 1:<br/>Data Collector]
    H --> J[MCP Server 2:<br/>Price Optimizer]
    
    I --> K[Tool: fetch_market_data]
    I --> L[Tool: get_recent_ticks]
    
    J --> M[Tool: get_product_info]
    J --> N[Tool: run_pricing_algorithm]
    
    G --> O[Direct Function Call:<br/>fetch_market_data]
    G --> P[Direct Function Call:<br/>get_product_info]
    
    K --> Q[Result]
    L --> Q
    M --> Q
    N --> Q
    O --> Q
    P --> Q
    
    style B fill:#fff4e1
    style F fill:#e1f5ff
    style G fill:#e1ffe1
```

**Key Points**:
- Single codebase supports both distributed (MCP) and local modes
- Factory functions abstract mode selection
- Connection pooling + retry logic for MCP resilience
- Auth capabilities for multi-tenant deployments

---

## Component Interaction Overview

```mermaid
graph TB
    subgraph Frontend
        A[React Components] --> B[Zustand Stores]
        B --> C[React Query Hooks]
        C --> D[API Client]
        D --> E[SSE Client]
    end
    
    subgraph Backend API
        F[FastAPI Endpoints] --> G[Dependency Injection]
        G --> H[Current User]
        G --> I[DataRepo]
        F --> J[SSE Streaming]
    end
    
    subgraph Core Business Logic
        K[Supervisor Agent] --> L[Tool Registry]
        M[LLM Client] --> N[Multi-Provider Failover]
        O[Chat Executor] --> L
        P[Event Bus] --> Q[Event Journal]
    end
    
    subgraph Specialized Agents
        R[Pricing Optimizer] --> M
        S[Data Collector] --> T[Connectors]
        U[Auto Applier] --> V[Decision Log]
        W[Governance Agent] --> V
    end
    
    subgraph Data Layer
        X[(app/data.db)]
        Y[(market.db)]
        Z[(auth.db)]
        AA[events.jsonl]
    end
    
    E -.->|HTTP/SSE| J
    J --> K
    K --> P
    P --> R
    P --> S
    P --> U
    P --> W
    
    R --> X
    S --> Y
    I --> X
    I --> Y
    I --> Z
    Q --> AA
    V --> X
    
    style Frontend fill:#e1f5ff
    style Backend API fill:#fff4e1
    style Core Business Logic fill:#e1ffe1
    style Specialized Agents fill:#ffe1f5
    style Data Layer fill:#f0f0f0
```

**Key Points**:
- Clean separation: Frontend (UI) → Backend (API) → Core (Business Logic) → Data
- Event Bus enables agent coordination without tight coupling
- LLM Client provides AI capabilities to autonomous agents
- All events journaled for observability

---

## Technology Stack Diagram

```mermaid
graph LR
    subgraph Frontend Stack
        A[React 18] --> B[TypeScript 5]
        B --> C[Vite]
        C --> D[Tailwind CSS]
        D --> E[Radix UI]
        A --> F[Zustand]
        A --> G[TanStack Query]
        A --> H[Vitest/Playwright]
    end
    
    subgraph Backend Stack
        I[FastAPI] --> J[Python 3.11+]
        J --> K[SQLAlchemy]
        K --> L[SQLite]
        J --> M[Pydantic]
        J --> N[pytest]
    end
    
    subgraph AI/ML Stack
        O[OpenAI API] --> P[LLM Orchestration]
        Q[OpenRouter] --> P
        R[Google Gemini] --> P
        P --> S[Tool Calling]
        P --> T[Streaming]
    end
    
    subgraph Infrastructure
        U[Event Bus] --> V[Pub/Sub Pattern]
        W[MCP Protocol] --> X[Distributed Agents]
        Y[SSE] --> Z[Real-time Updates]
    end
    
    Frontend Stack -.->|HTTP/SSE| Backend Stack
    Backend Stack --> AI/ML Stack
    Backend Stack --> Infrastructure
    
    style Frontend Stack fill:#e1f5ff
    style Backend Stack fill:#fff4e1
    style AI/ML Stack fill:#e1ffe1
    style Infrastructure fill:#ffe1f5
```

---

## Deployment Architecture Options

### Development Mode (USE_MCP=false)
```mermaid
graph TD
    A[Developer Machine] --> B[Single Process]
    B --> C[FastAPI Backend]
    B --> D[Vite Dev Server]
    
    C --> E[Local Agent Functions]
    E --> F[Data Collector]
    E --> G[Price Optimizer]
    E --> H[Auto Applier]
    
    C --> I[(SQLite DBs)]
    
    style B fill:#e1f5ff
```

### Production Mode (USE_MCP=true)
```mermaid
graph TD
    A[Load Balancer] --> B[FastAPI Instance 1]
    A --> C[FastAPI Instance 2]
    A --> D[FastAPI Instance N]
    
    B --> E[MCP Client Pool]
    C --> E
    D --> E
    
    E --> F[MCP Server:<br/>Data Collector]
    E --> G[MCP Server:<br/>Price Optimizer]
    E --> H[MCP Server:<br/>Governance]
    
    F --> I[(Shared SQLite<br/>or PostgreSQL)]
    G --> I
    H --> I
    
    B --> J[Event Bus Instance]
    C --> J
    D --> J
    
    J --> K[events.jsonl<br/>or Event Store]
    
    style E fill:#fff4e1
    style J fill:#e1ffe1
```

**Key Points**:
- Development: All-in-one process for fast iteration
- Production: Distributed agents via MCP for scalability
- Shared event bus enables cross-instance coordination
- Database can scale from SQLite (dev) to PostgreSQL (prod)
