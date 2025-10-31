# Alert Agent UI Analysis Report

## Executive Summary

This report documents how the Alert Agent's work is surfaced to users in the frontend UI, analyzing the complete data flow from backend detection through frontend display.

---

## 1. Backend Alert Generation

### 1.1 Alert Service Architecture

**Location**: `core/agents/alert_service/`

The Alert Agent operates through multiple components:

- **Engine** (`engine.py`): Core processing engine with LLM integration
- **Rules** (`rules.py`): Rule evaluation and detector logic
- **Detectors** (`detectors.py`): Statistical anomaly detection (EWMA Z-score)
- **Tools** (`tools.py`): LLM-accessible functions for alert creation
- **API** (`api.py`): High-level interface for incident management
- **Repo** (`repo.py`): Database persistence layer

### 1.2 LLM Alert Generation

**Key File**: `core/agents/alert_service/tools.py:164-203`

When the LLM detects an anomaly, it calls the `create_alert` tool:

```python
async def execute_tool_call(tool_name: str, tool_args: dict, tools_instance: Tools):
    if tool_name == "create_alert":
        alert = Alert(
            id=f"a_{int(now.timestamp()*1000)}",
            rule_id="llm_agent",              # Identifier for LLM-generated alerts
            sku=sku,
            title=name,
            payload=details,
            severity=severity,                 # Mapped from LOW/MEDIUM/HIGH to info/warn/crit
            ts=now,
            fingerprint=f"llm_agent:{name}:{sku}",
            owner_id=owner_id,
        )
        
        incident = await tools_instance.repo.find_or_create_incident(alert)
```

**Critical Identifier**: `rule_id="llm_agent"` - This is how the frontend distinguishes LLM-generated alerts from rule-based alerts.

### 1.3 LLM Tools Available

**Location**: `core/agents/alert_service/tools.py:85-147`

The LLM has access to three tools:

1. **list_rules**: Fetch active monitoring rules
2. **list_alerts**: Query existing alerts by status (OPEN/ACKED/RESOLVED)
3. **create_alert**: Generate new alerts with name, description, severity, and details

---

## 2. Backend API Endpoints

**Location**: `backend/routers/alerts.py`

Three REST endpoints expose alert data:

### 2.1 GET `/api/alerts/incidents`

```python
@router.get("/incidents")
async def get_incidents(status: Optional[str] = None, token: Optional[str] = None):
    sess = validate_session_token(token)
    owner_id = str(sess["user_id"])
    incidents = await alert_api.list_incidents(status, owner_id)
    return incidents
```

**Features**:
- Authentication required
- Filters by user ownership
- Optional status filtering
- Returns list of incident dictionaries

### 2.2 POST `/api/alerts/incidents/{incident_id}/ack`

```python
@router.post("/incidents/{incident_id}/ack")
async def acknowledge_incident(incident_id: str, token: Optional[str] = None):
    owner_id = str(sess["user_id"])
    result = await alert_api.ack_incident(incident_id, owner_id)
    return result
```

**Action**: Changes incident status from OPEN → ACKED

### 2.3 POST `/api/alerts/incidents/{incident_id}/resolve`

```python
@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, token: Optional[str] = None):
    owner_id = str(sess["user_id"])
    result = await alert_api.resolve_incident(incident_id, owner_id)
    return result
```

**Action**: Changes incident status from OPEN/ACKED → RESOLVED

---

## 3. Frontend Data Layer

### 3.1 TypeScript Type Definition

**Location**: `frontend/src/hooks/useIncidents.ts:4-13`

```typescript
export interface Incident {
  id: string
  rule_id: string                           // "llm_agent" for LLM alerts
  sku: string
  status: 'OPEN' | 'ACKED' | 'RESOLVED'
  first_seen: string
  last_seen: string
  severity: 'info' | 'warn' | 'crit'
  title: string
}
```

### 3.2 React Hook: useIncidents

**Location**: `frontend/src/hooks/useIncidents.ts:15-69`

**Key Features**:

```typescript
export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  
  // Fetches incidents every 30 seconds
  useEffect(() => {
    fetchIncidents()
    const interval = setInterval(fetchIncidents, 30000)
    return () => clearInterval(interval)
  }, [fetchIncidents])
  
  // Filters to show only active incidents
  const response = await fetch(`/api/alerts/incidents?token=${token}`)
  setIncidents(data.filter((i: Incident) => 
    i.status === 'OPEN' || i.status === 'ACKED'
  ))
  
  return {
    incidents,
    acknowledgeIncident,
    resolveIncident,
    refetch: fetchIncidents,
  }
}
```

**Polling**: 30-second refresh interval for real-time updates
**Filtering**: Only OPEN and ACKED incidents are displayed (RESOLVED are hidden)

---

## 4. Frontend UI Components

### 4.1 Main Display: PricesPanel

**Location**: `frontend/src/components/PricesPanel.tsx`

The `PricesPanel` is the primary interface for displaying alerts alongside price data.

#### Component Structure

```typescript
export function PricesPanel() {
  const { incidents, acknowledgeIncident, resolveIncident } = useIncidents()
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  
  // Maps incidents to SKUs for inline display
  const incidentsBySku = useMemo(() => {
    const map: Record<string, Incident> = {}
    incidents.forEach((inc) => {
      if (!map[inc.sku] || map[inc.sku].severity === 'info') {
        map[inc.sku] = inc  // Prioritizes higher severity
      }
    })
    return map
  }, [incidents])
  
  return (
    <aside className="w-[280px] border-l p-4">
      {/* Standalone alerts section */}
      {/* Price cards with attached alerts */}
      <AlertDetailModal />
    </aside>
  )
}
```

#### 4.1.1 Standalone Alerts Section

**Location**: `PricesPanel.tsx:227-285`

For incidents without corresponding price data:

```typescript
<div className="space-y-2 mb-4">
  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
    Alerts
  </div>
  {incidents
    .filter((i) => !incidentsBySku[i.sku] || keys.length === 0)
    .map((incident) => {
      const isLLM = incident.rule_id === 'llm_agent'
      return (
        <div className="p-3 rounded-lg border-2">
          <div className="flex items-start gap-2 mb-2">
            <IncidentIcon />
            <div className="flex-1">
              <div className="font-semibold text-xs">{incident.title}</div>
              <div className="text-[10px]">SKU: {incident.sku}</div>
              {isLLM && (
                <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-purple-500/30 text-purple-300">
                  <Bot className="h-3 w-3" />
                  <span>AI</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex gap-1">
            <button onClick={() => handleAlertClick(incident)}>Details</button>
            {incident.status === 'OPEN' && (
              <>
                <button onClick={() => acknowledgeIncident(incident.id)}>Ack</button>
                <button onClick={() => resolveIncident(incident.id)}>Resolve</button>
              </>
            )}
          </div>
        </div>
      )
    })}
</div>
```

#### 4.1.2 Inline Alerts on Price Cards

**Location**: `PricesPanel.tsx:31-131` (PriceCard component)

Alerts are displayed directly on the price card for the affected SKU:

```typescript
const PriceCardComponent = ({ k, data, alert, onAlertClick, onAcknowledge, onResolve }) => {
  const isLLM = alert?.rule_id === 'llm_agent'
  const severity = alert ? SEVERITY_CONFIG[alert.severity] : null
  
  return (
    <div className={`border rounded-lg ${
      alert ? `border-2 ${severity?.text.replace('text-', 'border-')}` : ''
    }`}>
      <div className="flex justify-between items-center">
        <span>{k}</span>
        <div>${last?.toFixed?.(2) ?? '-'}</div>
      </div>
      
      {/* Price visualization (sparkline/chart) */}
      
      {alert && (
        <div className="mt-3 pt-3 border-t">
          <div className="flex items-start gap-2 mb-2">
            <SeverityIcon />
            <div className="flex-1">
              <div className="font-semibold text-xs">{alert.title}</div>
              {isLLM && (
                <div className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-purple-500/30 text-purple-300">
                  <Bot className="h-3 w-3" />
                  <span>AI</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex gap-1">
            <button onClick={() => onAlertClick?.(alert)}>Details</button>
            {alert.status === 'OPEN' && (
              <>
                <button onClick={() => onAcknowledge?.(alert.id)}>Ack</button>
                <button onClick={() => onResolve?.(alert.id)}>Resolve</button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
```

**Visual Features**:
- **Border highlighting**: Color-coded by severity (blue=info, yellow=warn, red=crit)
- **AI Badge**: Purple badge with robot icon for LLM-generated alerts
- **Severity icon**: Visual indicator (ℹ️ / ⚠️ / 🚨)
- **Action buttons**: Details, Acknowledge, Resolve

### 4.2 Detail View: AlertDetailModal

**Location**: `frontend/src/components/AlertDetailModal.tsx:35-141`

Modal dialog for viewing full alert details:

```typescript
export function AlertDetailModal({ incident, open, onOpenChange, onAcknowledge, onResolve }) {
  if (!incident) return null
  
  const isLLM = incident.rule_id === 'llm_agent'
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>{severity.icon}</span>
            <span>{incident.title}</span>
            {isLLM && (
              <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-purple-500/30 text-purple-300">
                <span>🤖</span>
                <span>AI Generated</span>
              </div>
            )}
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-muted-foreground mb-1">SKU</div>
              <div className="font-mono text-sm">{incident.sku}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Status</div>
              <div className="inline-flex px-2 py-1 rounded text-xs">
                {status.label}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Severity</div>
              <div>{severity.label}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Rule ID</div>
              <div className="font-mono text-xs">{incident.rule_id}</div>
            </div>
          </div>
          
          <div className="border-t pt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-muted-foreground mb-1">First Seen</div>
                <div>{new Date(incident.first_seen).toLocaleString()}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground mb-1">Last Seen</div>
                <div>{new Date(incident.last_seen).toLocaleString()}</div>
              </div>
            </div>
          </div>
          
          {isLLM && (
            <div className="border-t pt-4">
              <div className="text-sm text-muted-foreground mb-2">
                This alert was generated by the AI Agent analyzing pricing anomalies and market
                conditions.
              </div>
            </div>
          )}
          
          {incident.status === 'OPEN' && (
            <div className="flex gap-2 pt-4 border-t">
              <Button onClick={() => onAcknowledge(incident.id)} variant="outline">
                Acknowledge
              </Button>
              <Button onClick={() => onResolve(incident.id)}>
                Resolve
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

**Features**:
- Full incident metadata display
- Timestamp information (first_seen, last_seen)
- Special AI-generated alert callout
- Action buttons (conditionally shown for OPEN incidents)

---

## 5. Visual Design System

### 5.1 Severity Configuration

```typescript
const SEVERITY_CONFIG = {
  info: { 
    bg: 'bg-blue-500/20', 
    text: 'text-blue-400', 
    label: 'Info', 
    icon: Info 
  },
  warn: { 
    bg: 'bg-yellow-500/20', 
    text: 'text-yellow-400', 
    label: 'Warning', 
    icon: AlertTriangle 
  },
  crit: { 
    bg: 'bg-red-500/20', 
    text: 'text-red-400', 
    label: 'Critical', 
    icon: AlertCircle 
  },
}
```

### 5.2 Status Configuration

```typescript
const STATUS_CONFIG = {
  OPEN: { 
    bg: 'bg-red-500/20', 
    text: 'text-red-400', 
    label: 'Open' 
  },
  ACKED: { 
    bg: 'bg-yellow-500/20', 
    text: 'text-yellow-400', 
    label: 'Acknowledged' 
  },
  RESOLVED: { 
    bg: 'bg-green-500/20', 
    text: 'text-green-400', 
    label: 'Resolved' 
  },
}
```

### 5.3 AI Badge Styling

LLM-generated alerts are distinguished with:

```css
bg-purple-500/30       /* Background: 30% opacity purple */
text-purple-300        /* Text: lighter purple */
border-purple-400/30   /* Border: 30% opacity darker purple */
```

**Icons**:
- Modal: 🤖 emoji
- Inline: `<Bot>` Lucide icon

---

## 6. User Interaction Flow

### 6.1 Alert Lifecycle

```
1. LLM detects anomaly
   ↓
2. create_alert tool called
   ↓
3. Alert saved to database with rule_id="llm_agent"
   ↓
4. Frontend polls every 30s via useIncidents hook
   ↓
5. Alert appears in UI:
   - Standalone section (if no price data)
   - Inline on price card (if price data exists)
   ↓
6. User actions:
   - Click "Details" → Opens AlertDetailModal
   - Click "Ack" → Status: OPEN → ACKED
   - Click "Resolve" → Status: OPEN/ACKED → RESOLVED
   ↓
7. Resolved alerts are filtered out of UI
```

### 6.2 User Actions

#### View Alert Details
1. User clicks "Details" button
2. `handleAlertClick(incident)` called
3. Sets `selectedIncident` state
4. `AlertDetailModal` opens with full incident data

#### Acknowledge Alert
1. User clicks "Ack" button
2. `acknowledgeIncident(incident.id)` called
3. POST request to `/api/alerts/incidents/{id}/ack`
4. Backend updates status to ACKED
5. Frontend refetches incidents
6. Alert remains visible with "Acknowledged" status
7. Only "Resolve" button shown

#### Resolve Alert
1. User clicks "Resolve" button
2. `resolveIncident(incident.id)` called
3. POST request to `/api/alerts/incidents/{id}/resolve`
4. Backend updates status to RESOLVED
5. Frontend refetches incidents
6. Alert is filtered out (no longer displayed)

---

## 7. Key Distinguishing Features for LLM Alerts

### 7.1 Backend Identifier
- `rule_id: "llm_agent"`
- `fingerprint: "llm_agent:{name}:{sku}"`

### 7.2 Frontend Detection
```typescript
const isLLM = incident.rule_id === 'llm_agent'
```

### 7.3 Visual Differentiation

**1. AI Badge**
- Purple-themed badge with robot icon
- Appears on both inline alerts and modal
- Text: "AI" (inline) or "AI Generated" (modal)

**2. Special Callout in Modal**
```
"This alert was generated by the AI Agent analyzing pricing anomalies 
and market conditions."
```

**3. No Additional Filtering**
- LLM alerts appear in the same stream as rule-based alerts
- Same severity/status coloring applies
- Same user actions available

---

## 8. Technical Considerations

### 8.1 Real-time Updates
- **Polling interval**: 30 seconds
- **Not true real-time**: Could be improved with WebSocket connection
- **Trade-off**: Simplicity vs. immediacy

### 8.2 State Management
- Local React state (useState)
- No global state management (Redux/Zustand)
- Each component manages its own alert state

### 8.3 Performance
- **Memo optimization**: `PriceCard` wrapped in `React.memo`
- **Incident mapping**: Computed once via `useMemo`
- **Prioritization**: Higher severity alerts override lower ones per SKU

### 8.4 Accessibility
- Semantic HTML structure
- ARIA labels on interactive elements
- Color is not the only differentiator (icons + text labels)

---

## 9. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       ALERT AGENT BACKEND                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌─────────────┐      ┌──────────────┐  │
│  │ AlertEngine  │ ───> │ LLM Agent   │ ───> │ Tools        │  │
│  │ (engine.py)  │      │ (with tools)│      │ (tools.py)   │  │
│  └──────────────┘      └─────────────┘      └──────────────┘  │
│         │                     │                      │          │
│         │                     │                      ↓          │
│         │                     │              create_alert()     │
│         │                     │                      │          │
│         ↓                     ↓                      ↓          │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                 Repository (repo.py)                    │   │
│  │          find_or_create_incident(alert)                 │   │
│  └────────────────────────────────────────────────────────┘   │
│                                │                                │
│                                ↓                                │
│                          [Database]                             │
│                 incidents table (rule_id="llm_agent")           │
│                                                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                       REST API LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GET  /api/alerts/incidents?token={token}&status={status}       │
│  POST /api/alerts/incidents/{id}/ack?token={token}              │
│  POST /api/alerts/incidents/{id}/resolve?token={token}          │
│                                                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND DATA LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  useIncidents Hook (useIncidents.ts)                 │      │
│  │  - Polls every 30s                                    │      │
│  │  - Filters: status === 'OPEN' || status === 'ACKED'  │      │
│  │  - Returns: incidents[], acknowledgeIncident(),      │      │
│  │             resolveIncident(), refetch()              │      │
│  └────────────────────┬─────────────────────────────────┘      │
│                       │                                          │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│                        UI COMPONENTS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  PricesPanel (PricesPanel.tsx)                         │    │
│  │                                                         │    │
│  │  ┌──────────────────────────────────────────────────┐ │    │
│  │  │ Standalone Alerts Section                        │ │    │
│  │  │ - For incidents without price data               │ │    │
│  │  │ - Shows: Title, SKU, AI badge (if LLM)           │ │    │
│  │  │ - Actions: Details, Ack, Resolve                 │ │    │
│  │  └──────────────────────────────────────────────────┘ │    │
│  │                                                         │    │
│  │  ┌──────────────────────────────────────────────────┐ │    │
│  │  │ PriceCard Components                             │ │    │
│  │  │ - Price data + inline alert                      │ │    │
│  │  │ - Severity-colored border                        │ │    │
│  │  │ - AI badge (if rule_id === 'llm_agent')          │ │    │
│  │  │ - Actions: Details, Ack, Resolve                 │ │    │
│  │  └──────────────────────────────────────────────────┘ │    │
│  │                                                         │    │
│  │  ┌──────────────────────────────────────────────────┐ │    │
│  │  │ AlertDetailModal (AlertDetailModal.tsx)          │ │    │
│  │  │ - Full incident metadata                         │ │    │
│  │  │ - AI Generated badge + callout                   │ │    │
│  │  │ - Timestamps (first_seen, last_seen)             │ │    │
│  │  │ - Rule ID, severity, status                      │ │    │
│  │  │ - Action buttons: Acknowledge, Resolve           │ │    │
│  │  └──────────────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Comparison: LLM Alerts vs Rule-Based Alerts

| Aspect | LLM Alerts | Rule-Based Alerts |
|--------|-----------|-------------------|
| **rule_id** | `"llm_agent"` | Rule-specific ID (e.g., `"price_spike"`) |
| **Creation** | LLM calls `create_alert` tool | Rule evaluation in AlertEngine |
| **Title** | Generated by LLM | Defined in rule spec |
| **Description** | LLM-generated context | Rule template |
| **Severity mapping** | LOW/MEDIUM/HIGH → info/warn/crit | Direct: info/warn/crit |
| **Visual badge** | Purple "AI" badge | No special badge |
| **Modal callout** | "This alert was generated by the AI Agent..." | No special callout |
| **Fingerprint** | `llm_agent:{name}:{sku}` | Rule-specific pattern |
| **User actions** | Identical (Ack, Resolve, Details) | Identical |
| **Display location** | Same as rule-based | Same as LLM |
| **Filtering** | Same (OPEN/ACKED only) | Same (OPEN/ACKED only) |

---

## 11. Potential Improvements

### 11.1 Real-time Communication
- **Current**: 30-second polling
- **Improvement**: WebSocket connection for instant alerts
- **Benefit**: Reduces latency, lower server load

### 11.2 Alert History View
- **Current**: RESOLVED alerts are hidden
- **Improvement**: Dedicated history page with filters
- **Benefit**: Audit trail, pattern analysis

### 11.3 Enhanced LLM Context
- **Current**: Limited metadata in UI
- **Improvement**: Show LLM reasoning, confidence score
- **Benefit**: Transparency, trust-building

### 11.4 Notification System
- **Current**: In-app only
- **Improvement**: Browser notifications, email, Slack
- **Benefit**: Proactive alerting

### 11.5 Alert Analytics
- **Current**: No aggregation
- **Improvement**: Dashboard with trends, frequency charts
- **Benefit**: Pattern recognition, KPI tracking

### 11.6 Bulk Actions
- **Current**: One-at-a-time acknowledgment
- **Improvement**: Multi-select + bulk Ack/Resolve
- **Benefit**: Efficiency for high-alert scenarios

### 11.7 Alert Comments/Notes
- **Current**: No user annotations
- **Improvement**: Add comments to incidents
- **Benefit**: Team collaboration, context preservation

---

## 12. Conclusion

The Alert Agent's work is comprehensively surfaced to users through a well-integrated UI system:

### ✅ Strengths

1. **Clear visual differentiation**: LLM alerts are easily identifiable with AI badges
2. **Contextual display**: Alerts appear both standalone and inline with price data
3. **Full lifecycle support**: Users can view, acknowledge, and resolve alerts
4. **Consistent UX**: Same interaction patterns for LLM and rule-based alerts
5. **Severity-based visual hierarchy**: Color-coded borders and icons aid quick triage
6. **Regular updates**: 30-second polling keeps data reasonably fresh

### 🔄 Areas for Enhancement

1. **Real-time updates**: Move from polling to WebSocket push
2. **Alert history**: Surface resolved alerts for audit and analysis
3. **Enhanced metadata**: Show more LLM reasoning/context
4. **Notification channels**: Extend beyond in-app display
5. **Analytics dashboard**: Aggregate and visualize alert patterns

### 📊 Current Impact

The Alert Agent successfully:
- Generates intelligent, context-aware alerts via LLM
- Surfaces alerts prominently in the primary pricing interface
- Provides clear visual cues for AI-generated insights
- Enables user feedback loop (Ack/Resolve actions)
- Maintains separation of concerns (backend logic, frontend display)

**Overall Assessment**: The system effectively communicates Alert Agent insights to users, with a solid foundation for future enhancements.

---

## Appendix: File Reference Index

### Backend Files
- `backend/routers/alerts.py` - REST API endpoints
- `core/agents/alert_service/engine.py` - Alert processing engine
- `core/agents/alert_service/tools.py` - LLM tool definitions and execution
- `core/agents/alert_service/api.py` - High-level service API
- `core/agents/alert_service/rules.py` - Rule evaluation logic
- `core/agents/alert_service/detectors.py` - Anomaly detection algorithms
- `core/agents/alert_service/repo.py` - Database persistence
- `core/agents/alert_service/schemas.py` - Data models

### Frontend Files
- `frontend/src/hooks/useIncidents.ts` - Data fetching hook
- `frontend/src/components/PricesPanel.tsx` - Main alert display component
- `frontend/src/components/AlertDetailModal.tsx` - Alert detail modal
- `frontend/src/pages/PricingPage.tsx` - Page containing PricesPanel

### Test Files
- `scripts/test_llm_alert_agent.py` - LLM alert agent testing
- `scripts/test_llm_single_alert.py` - Single alert testing

---

**Report Generated**: 2025-10-19  
**System Version**: Dynamic Pricing AI Platform v1.0  
**Author**: AI Analysis System
