# MCP Server Implementation Plan

## Overview
This plan activates the dormant MCP servers in the dynamic pricing system, converting them from stubs into production-ready services.

## Focus Areas
- **SDK/Transport**: Decide stdio vs WebSocket and Python MCP library
- **Contracts**: Lock down tool names, inputs/outputs, and error schemas  
- **Services**: Alerts, Data Collector, Price Optimizer as separate servers
- **Client/Runtime**: Harden `agent_sdk/mcp_client.py`, integrate with supervisor/bus
- **Quality**: Tests, authZ, observability, and rollout discipline

## Implementation Tasks

### Foundation (High Priority)
- [ ] **SDK Choice**: Select MCP SDK, transport (stdio/websocket), and version; document choices
- [ ] **Audit Stubs**: Audit existing MCP stubs and list target tools per service (alerts, data, optimizer)
- [ ] **Contracts**: Define tool contracts and JSON schemas for each service (inputs/outputs, errors)

### Service Implementation (High Priority)
- [ ] **Alert Service**: Implement MCP tools (list/create/ack/resolve/subscribe) with validation
- [ ] **Data Collector**: Implement MCP tools (list_sources/fetch/ingest/status) with validation  
- [ ] **Price Optimizer**: Implement MCP tools (propose_price/explain/apply/cancel) with validation
- [ ] **Health Tools**: Add health/version/ping tool to every MCP server

### Infrastructure (High Priority)
- [ ] **CLI Entrypoints**: Create CLI entrypoints to run each server with config (env/ports/stdio)
- [ ] **Client Hardening**: Harden `agent_sdk/mcp_client.py` (timeouts, retries, reconnect, pooling)
- [ ] **Supervisor Integration**: Integrate servers with supervisor/event bus; lifecycle management and backoff
- [ ] **Authorization**: Add authN/Z for tool execution; scope tokens and enforce roles

### Quality Assurance (High Priority)
- [ ] **Unit Tests**: Write unit tests for tool handlers and schema validation
- [ ] **Integration Tests**: Add integration tests that launch servers and call via client

### Integration & Operations (Medium Priority)
- [ ] **Observability**: Wire structured logging/metrics/tracing; attach request IDs to calls
- [ ] **UI/Backend Integration**: Expose MCP-backed actions in backend/UI where relevant (Streamlit and APIs)
- [ ] **Documentation**: Setup, running locally/CI, contracts, troubleshooting
- [ ] **Dev Scripts**: Dev scripts for local run and CI orchestration; update repo scripts
- [ ] **CI Pipeline**: CI updates: lint/type/test jobs for MCP modules; basic health check
- [ ] **Acceptance/SLOs**: Define acceptance criteria and SLOs (latency, reliability, coverage)

### Rollout (Low Priority)
- [ ] **Rollout Plan**: Rollout plan with feature flags, canary, and fallback path

## Service Tool Specifications

### Alert Service Tools
- `list_alerts` - List active alerts with filters
- `create_alert` - Create new alert with validation
- `ack_alert` - Acknowledge alert by ID
- `resolve_alert` - Mark alert as resolved
- `subscribe_alerts` - Subscribe to alert notifications

### Data Collector Tools
- `list_sources` - List available data sources
- `fetch_sample` - Fetch sample data from source
- `ingest_now` - Trigger immediate data ingestion
- `job_status` - Check ingestion job status

### Price Optimizer Tools
- `propose_price` - Generate price proposal for product
- `explain_proposal` - Explain reasoning behind proposal
- `apply_proposal` - Apply approved price proposal
- `cancel_proposal` - Cancel pending proposal

### Health/Meta Tools (All Servers)
- `ping` - Basic connectivity check
- `health` - Detailed health status
- `version` - Server version info
- `capabilities` - Available tools list

## Acceptance Criteria & SLOs

### Performance
- **Latency p95**: Alerts/Data tools ≤ 300ms; Optimizer ≤ 800ms
- **Availability**: ≥ 99.5% during canary; error rate < 1%

### Coverage
- Tools implemented and tested per service list
- All existing functionality accessible via MCP

### Security
- AuthZ enforced on all tool calls
- No secrets leaked in logs or responses
- Token-based authentication for WebSocket transport

## Open Questions
1. Preferred transport per environment (local dev vs prod)?
2. Which service to canary first?
3. Any additional tools needed beyond the three service sets?

## Progress Tracking
This plan is tracked via TODO system. Tasks are marked as:
- `pending` - Not yet started
- `in_progress` - Currently working on
- `completed` - Finished successfully
- `cancelled` - No longer needed