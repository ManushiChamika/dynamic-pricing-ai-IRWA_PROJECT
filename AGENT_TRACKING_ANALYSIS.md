# Agent Tracking & Metadata Analysis Report

## Executive Summary
Agent metadata IS being captured and stored in the database, and IS being sent to the frontend in the SSE stream. The "agents 2" badge appears in the header showing that agents are being tracked correctly. However, agent details are currently only visible in:
1. A tooltip via the info icon on individual messages (MetadataTooltip)
2. The real-time "agents X" badge during streaming in ChatHeader
3. The post-streaming "agents X" badge and tooltip when stream completes

---

## 1. Data Structure for Agent Tracking

### Database Level (core/chat_db.py:55)
```python
class Message(Base):
    agents = Column(Text, nullable=True)     # JSON string
```

**Format stored in DB:**
```json
{
  "activated": ["agent_name_1", "agent_name_2"],
  "count": 2
}
```

### Backend Capture (backend/routers/streaming.py:102)
Agents are tracked by intercepting events during the UserInteractionAgent workflow:

```python
activated_agents: set = set()  # Line 102

# During streaming (Line 223-226):
if et == "agent":
    agent_name = delta.get("name")
    if agent_name:
        activated_agents.add(agent_name)

# Converted to JSON object (Line 132):
agents_obj = {"activated": agents_list, "count": len(agents_list)}
```

---

## 2. Where "agents 2" Count Comes From

### The Complete Flow:

#### A. Backend Capture (streaming.py:100-160)
1. **Set created**: `activated_agents: set = set()` at line 102
2. **Events parsed**: When processing events from UserInteractionAgent
   - Event type "agent" triggers agent name extraction
   - Agent names added to set: `activated_agents.add(agent_name)`
3. **Count computed**: `len(agents_list)` where `agents_list = list(activated_agents)`

#### B. Backend Storage (streaming.py:130-160)
Creates JSON object:
```python
agents_obj = {"activated": agents_list, "count": len(agents_list)}
```

This is stored in the Message record:
- Line 139: Updates user message with agents
- Line 154: Adds agents to assistant message
- Line 309: Updates user message again (streaming path)
- Line 322: Updates assistant message (streaming path)

#### C. Backend Transmission (streaming.py:355)
Final SSE payload includes:
```python
payload = {
    ...
    "agents": agents_obj,  # {"activated": [...], "count": 2}
    ...
}
yield "event: message\n" + "data: " + _json.dumps(payload) + "\n\n"
```

#### D. Frontend Reception (frontend/src/lib/api/sseClient.ts:146-162)
SSE client parses the message event:
```typescript
if (ev === 'message' && data) {
    const obj = JSON.parse(data)
    if (obj.id) {
        const agents = (obj?.agents?.activated || []) as string[]
        const turnStats = {
            ...
            agents,  // Array of agent names
            ...
        }
        onUpdate({ turnStats })
    }
}
```

#### E. Frontend Store (frontend/src/stores/messageStore.ts:179-182)
```typescript
if (update.turnStats) {
    console.log('[MessageStore] Setting turnStats:', update.turnStats)
    return { turnStats: update.turnStats }
}
```

#### F. Frontend Display (frontend/src/components/chat/ChatHeader.tsx:233-240)
```typescript
{Array.isArray(turnStats.agents) && turnStats.agents.length ? (
    <span ... title={`Agents: ${turnStats.agents.join(', ')}`}>
        agents {turnStats.agents.length}
    </span>
) : null}
```

---

## 3. Database Schema & Agent Storage

### Message Table Schema (core/chat_db.py)
| Field | Type | Usage |
|-------|------|-------|
| id | Integer PK | Message ID |
| thread_id | Integer FK | Links to thread |
| role | String | 'user' \| 'assistant' \| 'tool' \| 'system' |
| content | Text | Message content |
| model | String | LLM model name |
| token_in | Integer | Input tokens |
| token_out | Integer | Output tokens |
| cost_usd | String | Estimated cost |
| api_calls | Integer | Number of API calls |
| **agents** | Text (JSON) | **`{"activated": [...], "count": N}`** |
| **tools** | Text (JSON) | **`{"used": [...], "count": N}`** |
| **meta** | Text (JSON) | **`{"provider": "...", "tools_used": [...]}`** |
| created_at | DateTime | Timestamp |

### Full Agent Flow in DB

1. **User sends message** → Added to DB with agents=NULL
2. **UserInteractionAgent processes** → Events tracked, agents collected
3. **Assistant responds** → New message added with agents JSON
4. **Both messages updated** → Agent info written to DB

**Example stored data:**
```sql
-- User message AFTER response:
agents: '{"activated": ["DataCollector", "PricingOptimizer"], "count": 2}'

-- Assistant message:
agents: '{"activated": ["DataCollector", "PricingOptimizer"], "count": 2}'
```

---

## 4. Frontend Metadata Display Components

### 4A. MetadataTooltip.tsx (Primary Display)
**Location**: frontend/src/components/MetadataTooltip.tsx
**What it shows**: Info icon with hover tooltip
**Agent data extraction** (lines 52-56):
```typescript
const agentNames = message.agents?.activated || []
const agentCount = message.agents?.count ?? agentNames.length
if (agentCount > 0) {
    info.push(`Agents: ${agentCount}${agentNames.length ? ` (${agentNames.join(', ')})` : ''}`)
}
```

**Tooltip display:**
```
Info icon (i) → Hover → Shows:
- Time: ...
- Model: ...
- Tokens: ...
- Cost: ...
- API Calls: ...
- Agents: 2 (DataCollector, PricingOptimizer)
- Tools: 3 (...)
```

### 4B. ChatHeader.tsx (Badge Display)
**Location**: frontend/src/components/chat/ChatHeader.tsx

**During streaming** (lines 172-179):
```typescript
{streamingActive && Array.isArray(liveAgents) && liveAgents.length ? (
    <span title={`Agents: ${liveAgents.join(', ')}`}>
        agents {liveAgents.length}
    </span>
) : null}
```

**After streaming** (lines 233-240):
```typescript
{Array.isArray(turnStats.agents) && turnStats.agents.length ? (
    <span title={`Agents: ${turnStats.agents.join(', ')}`}>
        agents {turnStats.agents.length}
    </span>
) : null}
```

### 4C. Message Model Definition (messageStore.ts)
**Location**: frontend/src/stores/messageStore.ts:14-29
```typescript
export type Message = {
    ...
    agents?: { activated?: string[]; count?: number } | null
    tools?: { used?: string[]; count?: number } | null
    metadata?: MessageMeta | null
    ...
}
```

---

## 5. What's Being Captured But NOT Displayed

### Data Captured but Underutilized:

#### A. Individual Agent Details
- **What's captured**: Each agent name in `agents.activated[]`
- **Current display**: Only shown in tooltip on hover
- **Not used for**: List views, summary pages, analytics

#### B. Agent Timing Information
- **Captured**: When each agent is activated (in event stream)
- **Not stored**: No timestamp for when each agent started/ended
- **Potential use**: Timeline visualization

#### C. Agent Execution Results
- **Not captured**: What each agent actually did or produced
- **Potential location**: Could be in event stream or tool results
- **Current gap**: Only count visible, not actions

#### D. Tool-Agent Relationships
- **Captured separately**: 
  - `agents: {"activated": [...], "count": 2}`
  - `tools: {"used": [...], "count": 3}`
- **Not linked**: No way to know which agent used which tool
- **Potential use**: Dependency tracking, tool usage analytics

#### E. Metadata Provider Info
- **Captured**: `metadata: {"provider": "openai", "tools_used": [...]}`
- **Current display**: Only model/provider shown in tooltip
- **Not used for**: Provider usage analytics

#### F. API Calls Detail
- **Captured**: `api_calls: 5`
- **Not captured**: Breakdown of which API was called (LLM vs tools)
- **Potential use**: Cost and performance analysis per agent

---

## 6. API Response Flow

### A. Get Messages Endpoint (backend/routers/messages.py:39-73)
Returns all thread messages with full agent data:
```python
def api_get_messages(thread_id: int):
    # Parses agents JSON and includes in response
    agents = _json.loads(m.agents) if m.agents else None
    
    out.append(MessageOut(
        ...
        agents=agents,  # {"activated": [...], "count": N}
        ...
    ))
```

### B. Export Thread Endpoint (backend/routers/threads.py:78-136)
Exports full agent metadata:
```python
item["agents"] = __import__("json").loads(m.agents)
```

### C. Import Thread Endpoint (backend/routers/threads.py:139-181)
Preserves agent data during import:
```python
agents = _json.dumps(msg.agents) if getattr(msg, 'agents', None) is not None else None
```

---

## 7. Frontend Store State Management

### messageStore.ts - TurnStats Definition (lines 54-63)
```typescript
turnStats: {
    token_in?: number | null
    token_out?: number | null
    cost_usd?: string | number | null
    api_calls?: number | null
    model?: string | null
    provider?: string | null
    agents?: string[]              // Array of agent names
    tools?: string[]               // Array of tool names
} | null
```

### State Updates
- **Set during streaming**: Line 179-182 when SSE message event received
- **Cleared on new message**: Line 104 when sending new message
- **Cleared on done**: Line 200 when streaming completes

---

## 8. Why Agent Details Aren't More Visible

### Current Visibility Status:
✅ **Visible**:
- Real-time "agents X" badge during streaming (ChatHeader)
- Post-stream "agents X" badge after completion (ChatHeader)
- Agent names in tooltip on hover (MetadataTooltip)
- Export/import preserves agent data
- API responses include agent data

❌ **Not Visible**:
- No dedicated agent panel or sidebar
- No agent-specific analytics dashboard
- No timeline showing agent execution order
- No per-agent statistics
- No agent-tool relationship visualization

### Design Rationale (Likely):
1. **Simplicity**: Keeps header clean, info accessible via tooltip
2. **Real estate**: Header space limited, badges are minimal
3. **Use case**: Dev debugging primary use case
4. **Future extensibility**: Data structure supports future agent visualization

---

## 9. Data Structure Summary Table

| Data Point | Captured | Stored | Transmitted | Displayed |
|-----------|----------|--------|-------------|-----------|
| Agent names | ✅ Yes | ✅ DB | ✅ SSE+API | ✅ Tooltip |
| Agent count | ✅ Yes | ✅ DB | ✅ SSE+API | ✅ Badge |
| Agent timing | ❌ No | ❌ No | ❌ No | ❌ No |
| Agent actions | ❌ No | ❌ No | ❌ No | ❌ No |
| Tool-agent map | ❌ No | ❌ No | ❌ No | ❌ No |
| Cost per agent | ❌ No | ❌ No | ❌ No | ❌ No |
| Provider info | ✅ Yes | ✅ DB | ✅ SSE+API | ✅ Tooltip |
| Total API calls | ✅ Yes | ✅ DB | ✅ SSE+API | ✅ Badge |

---

## 10. Key Findings

### The "agents 2" Badge
- **Source**: `turnStats.agents.length` from SSE message event
- **Populated by**: Backend counting unique agent events (activated_agents set)
- **Data integrity**: Accurate - tracks all agents that participated
- **Update timing**: Sent when streaming completes (final message event)

### What's Working Well
1. ✅ Agents are correctly identified and counted
2. ✅ Data flows end-to-end from backend to frontend
3. ✅ Data persists in database correctly
4. ✅ Export/import preserves agent data
5. ✅ API responses include full agent details

### What Could Be Improved
1. ⚠️ Agent execution timeline not captured
2. ⚠️ Agent actions/results not stored
3. ⚠️ No tool-to-agent relationship mapping
4. ⚠️ Agent-specific metrics not available
5. ⚠️ No agent-specific error tracking

---

## 11. How to Access Agent Data

### Via Frontend UI
1. **Live during streaming**: Watch "agents X" badge update in ChatHeader
2. **After completion**: Click info icon (i) on any message to see agent names
3. **Post-stream**: "agents X" badge shown in header with hoverable tooltip

### Via API
```bash
# Get all messages with agent data
GET /api/threads/{thread_id}/messages

# Export thread (includes agent data)
GET /api/threads/{thread_id}/export

# Import thread (preserves agent data)
POST /api/threads/import
```

### Via Database
```sql
SELECT id, agents, tools, content FROM messages 
WHERE thread_id = 1 AND agents IS NOT NULL;

-- agents column contains: {"activated": ["agent1", "agent2"], "count": 2}
```

---

## 12. Recommendations

### Short Term (Quick Wins)
1. **Agent list detail**: Expand tooltip to show agent names more prominently
2. **Hover state**: Style the agent badge to be more discoverable
3. **Documentation**: Document that info icon shows agent details

### Medium Term (Enhancement)
1. **Agent panel**: Add optional sidebar showing agent breakdown
2. **Agent timeline**: Add column showing agent execution order
3. **Per-agent stats**: Calculate and display cost/tokens per agent

### Long Term (Architecture)
1. **Event logging**: Store detailed agent events with timestamps
2. **Agent analytics**: Build dashboard showing agent usage patterns
3. **Tool-agent mapping**: Track which agent used which tool
4. **Agent profiles**: Store agent configuration and capabilities

