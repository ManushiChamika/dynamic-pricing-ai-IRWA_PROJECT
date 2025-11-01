# Legacy MCP Architecture Archive

## Overview

This directory contains MCP (Model Context Protocol) server implementations and infrastructure that were built but never integrated into the production system. These files represent an architectural path that was explored but ultimately not adopted in favor of Event Bus patterns and direct Python function calls.

## Why These Files Were Archived

Based on comprehensive codebase analysis documented in `docs/MCP_IMPLEMENTATION_ANALYSIS.md`, the production system uses:

1. **Event Bus Pattern** (Dominant): Alert Service, Auto Applier, Governance Agent
2. **Direct Python Calls**: Price Optimizer agent  
3. **MCP Protocol** (Limited): Only Data Collector agent uses MCP in production

The archived files represent fully-implemented MCP servers for Price Optimizer and Alert Service, along with their supporting infrastructure, but **no production code consumes these MCP servers**. They exist as complete but unused implementations.

## Archived Files (6 total)

### MCP Server Implementations (2 files)
- `core/agents/price_optimizer/mcp_server.py` (304 lines, 9 MCP tools)
  - Implements: `get_latest_proposal`, `apply_proposal`, `revert_proposal`, `list_proposals`, etc.
  - **Reality**: Production uses `core.agents.price_optimizer.agent.PricingOptimizerAgent` directly
  
- `core/agents/alert_service/mcp_server.py` (244 lines, 10 MCP tools)
  - Implements: `get_alerts`, `acknowledge_alert`, `configure_rules`, `test_rule`, etc.
  - **Reality**: Production uses `core.agents.alert_service.engine.AlertEngine` via event bus

### Startup Scripts (2 files)
- `scripts/run_price_optimizer_mcp.py` - Launcher for unused Price Optimizer MCP server
- `scripts/run_alerts_mcp.py` - Launcher for unused Alert Service MCP server

### Infrastructure Components (2 files)
- `scripts/mcp_server.py` (120 lines) - Unified CLI launcher for all MCP servers
  - Supported `data-collector`, `alerts`, `price-optimizer` services
  - **Reality**: Only `data-collector` is used; others never called
  
- `core/agents/agent_sdk/mcp_supervisor.py` (317 lines) - Process supervisor for MCP servers
  - Contains `MCPSupervisor` class with subprocess management
  - Defines `DEFAULT_SERVICES` config for all 3 MCP servers
  - **Reality**: Never instantiated in production; `supervisor.py` doesn't use it

## Production MCP Usage (ACTIVE)

The following MCP components remain in the active codebase and are used in production:

- ✅ `core/agents/data_collector/mcp_server.py` - Active, consumed by supervisor
- ✅ `core/agents/agent_sdk/mcp_client.py` - Active, used by supervisor to call Data Collector
- ✅ `scripts/run_data_collector_mcp.py` - Active startup script

## How to Restore (If Needed)

If you need to restore any archived files back to the active codebase:

```bash
# Restore specific file
git mv _legacy_mcp_archive/core/agents/price_optimizer/mcp_server.py core/agents/price_optimizer/mcp_server.py

# Restore all files
git mv _legacy_mcp_archive/core/agents/price_optimizer/mcp_server.py core/agents/price_optimizer/
git mv _legacy_mcp_archive/core/agents/alert_service/mcp_server.py core/agents/alert_service/
git mv _legacy_mcp_archive/scripts/run_price_optimizer_mcp.py scripts/
git mv _legacy_mcp_archive/scripts/run_alerts_mcp.py scripts/
git mv _legacy_mcp_archive/scripts/mcp_server.py scripts/
git mv _legacy_mcp_archive/core/agents/agent_sdk/mcp_supervisor.py core/agents/agent_sdk/
```

Then remove the archive directory:
```bash
rmdir /s _legacy_mcp_archive
```

## Validation Performed Before Archival

Before archiving, the following checks confirmed these files had no active consumers:

1. ✅ No import statements for `price_optimizer.mcp_server` or `alert_service.mcp_server`
2. ✅ No instantiation of `MCPSupervisor` class
3. ✅ No calls to `scripts/mcp_server.py` CLI launcher
4. ✅ Startup scripts not referenced in `run_full_app.bat` or automation
5. ✅ `supervisor.py` uses direct imports, not MCP clients for these agents
6. ✅ All production imports still work after archival

## References

- **Analysis Report**: `docs/MCP_IMPLEMENTATION_ANALYSIS.md`
- **Architecture Documentation**: `docs/system_architecture.mmd`
- **Active Supervisor**: `core/agents/supervisor.py`

## Archival Date

**Date**: October 19, 2025  
**Reason**: Align codebase with actual production architecture patterns  
**Reversibility**: Fully reversible via git operations shown above
