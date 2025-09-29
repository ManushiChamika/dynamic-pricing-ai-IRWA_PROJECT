# MCP Tool Contracts and JSON Schemas

This document reflects the current, real tool signatures and response shapes implemented in the MCP servers found under `core/agents/*/mcp_server.py`.

## Standard Error Response Schema

```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": false},
    "error": {"type": "string"},
    "error_code": {"type": "string"},
    "message": {"type": "string"},
    "details": {"type": ["object", "array", "string", "null"]}
  },
  "required": ["ok", "error"]
}
```

Notes:
- `error_code` values currently observed include `validation_error`, `auth_error`, `optimization_error`, and `legacy_call_error` (legacy optimize path). Not all errors include `error_code`.
- Some errors provide a `message` string; others include structured `details` (e.g., Pydantic validation errors).

## Health Tools (All Servers)

Actual tool names in services:
- `ping_health`: basic connectivity test
- `health_check`: detailed health status
- `version_info`: server version information

### ping_health
Input: none
Output:
```json
{
  "type": "object", 
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "timestamp": {"type": "string", "format": "date-time"}
  },
  "required": ["ok", "timestamp"]
}
```

### health_check
Input: none
Output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean"},
    "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
    "version": {"type": "string"},
    "uptime_seconds": {"type": ["number", "null"]},
    "dependencies": {
      "type": "object"
    }
  },
  "required": ["ok", "status", "version"]
}
```

### version_info
Input: none
Output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "version": {"type": "string"},
    "build": {"type": ["string", "null"]},
    "commit": {"type": ["string", "null"]}
  },
  "required": ["ok", "version"]
}
```

---

## Data Collector Service Tools
File: `core/agents/data_collector/mcp_server.py`

Authentication: where shown, tools require `capability_token` with appropriate scope (e.g., `collect`, `read`, `write`, `import`, `admin`).

### start_collection
Purpose: Start a background collection job.
Input:
```json
{
  "type": "object",
  "properties": {
    "sku": {"type": "string", "minLength": 1},
    "market": {"type": "string", "default": "DEFAULT"},
    "connector": {"type": "string", "enum": ["mock"], "default": "mock"},
    "depth": {"type": "integer", "minimum": 1, "maximum": 100, "default": 1},
    "capability_token": {"type": "string"}
  },
  "required": ["sku", "capability_token"],
  "additionalProperties": false
}
```
Successful output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "job_id": {"type": "string"},
    "sku": {"type": "string"},
    "market": {"type": "string"},
    "connector": {"type": "string", "enum": ["mock"]},
    "depth": {"type": "integer"}
  },
  "required": ["ok", "job_id", "sku", "market", "connector", "depth"]
}
```
Potential error (unsupported connector):
```json
{
  "ok": false,
  "error": "unsupported_connector",
  "supported_connectors": ["mock"]
}
```

### get_job_status
Purpose: Return current job status.
Input:
```json
{
  "type": "object",
  "properties": {
    "job_id": {"type": "string", "minLength": 1},
    "capability_token": {"type": "string"}
  },
  "required": ["job_id", "capability_token"],
  "additionalProperties": false
}
```
Output (shape of `job` depends on repository):
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean"},
    "job": {"type": ["object", "null"]},
    "job_id": {"type": "string"}
  },
  "required": ["ok", "job_id"]
}
```

### fetch_market_features
Purpose: Fetch market features for a SKU.
Input:
```json
{
  "type": "object",
  "properties": {
    "sku": {"type": "string", "minLength": 1},
    "market": {"type": "string", "default": "DEFAULT"},
    "time_window": {"type": "string", "pattern": "^P\\\d+D$", "default": "P7D"},
    "freshness_sla_minutes": {"type": "integer", "minimum": 1, "maximum": 1440, "default": 60},
    "capability_token": {"type": "string"}
  },
  "required": ["sku", "capability_token"],
  "additionalProperties": false
}
```
Output (flat structure with standard fields):
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean"},
    "sku": {"type": "string"},
    "market": {"type": "string"},
    "time_window": {"type": "string"}
  },
  "required": ["ok", "sku", "market", "time_window"],
  "additionalProperties": true
}
```
Notes:
- The response is not nested under `features`; instead, standard fields are included at the top level along with feature keys returned by the repository. In fallback paths, a legacy shape `{ ok, features: {...} }` may appear.

### ingest_tick
Purpose: Ingest a single market tick/document.
Input:
```json
{
  "type": "object",
  "properties": {
    "d": {"type": "object"},
    "capability_token": {"type": "string"}
  },
  "required": ["d", "capability_token"],
  "additionalProperties": false
}
```
Output:
```json
{ "ok": true }
```

### import_product_catalog
Purpose: Import or update products in the catalog.
Input:
```json
{
  "type": "object",
  "properties": {
    "rows": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sku": {"type": "string", "minLength": 1}
        },
        "required": ["sku"],
        "additionalProperties": true
      }
    },
    "capability_token": {"type": "string"}
  },
  "required": ["rows", "capability_token"],
  "additionalProperties": false
}
```
Output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "count": {"type": "integer"},
    "processed": {"type": "integer"},
    "total_input": {"type": "integer"}
  },
  "required": ["ok", "count", "processed", "total_input"]
}
```

### list_sources
Purpose: List available data sources and their status.
Input: none (requires `capability_token` with `read` scope if enforced in your environment).
Output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "sources": {
      "type": "array",
      "items": {
        "type": "object", 
        "properties": {
          "name": {"type": "string"},
          "type": {"type": "string", "enum": ["mock", "web_scraper"]},
          "status": {"type": "string", "enum": ["active", "inactive", "error"]},
          "description": {"type": "string"},
          "last_check": {"type": "string", "format": "date-time"}
        },
        "required": ["name", "type", "status"]
      }
    },
    "count": {"type": "integer"}
  },
  "required": ["ok", "sources"]
}
```

### auth_metrics
Purpose: Return authentication metrics (admin scope required).
Input:
```json
{
  "type": "object",
  "properties": {
    "capability_token": {"type": "string"}
  },
  "required": ["capability_token"],
  "additionalProperties": false
}
```
Output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "result": {
      "type": "object",
      "properties": {
        "service": {"type": "string"},
        "metrics": {"type": "object"},
        "timestamp": {"type": "string", "format": "date-time"}
      },
      "required": ["service", "metrics", "timestamp"]
    }
  },
  "required": ["ok", "result"]
}
```

---

## Price Optimizer Service Tools
File: `core/agents/price_optimizer/mcp_server.py`

Authentication: where shown, tools require `capability_token` with appropriate scope (e.g., `propose`, `explain`, `apply`, `admin`).

### propose_price
Purpose: Generate a price optimization proposal.
Input:
```json
{
  "type": "object",
  "properties": {
    "sku": {"type": "string", "minLength": 1},
    "our_price": {"type": "number", "exclusiveMinimum": 0},
    "competitor_price": {"type": ["number", "null"], "exclusiveMinimum": 0},
    "demand_index": {"type": ["number", "null"], "minimum": 0},
    "cost": {"type": ["number", "null"], "minimum": 0},
    "min_price": {"type": ["number", "null"], "minimum": 0, "default": 0},
    "max_price": {"type": ["number", "null"], "minimum": 0},
    "min_margin": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.12},
    "capability_token": {"type": "string"}
  },
  "required": ["sku", "our_price", "capability_token"],
  "additionalProperties": false
}
```
Output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "proposal": {
      "type": "object",
      "properties": {
        "proposal_id": {"type": "string"},
        "sku": {"type": "string"},
        "current_price": {"type": "number"},
        "proposed_price": {"type": "number"},
        "expected_margin": {"type": "number"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning": {"type": "string"},
        "expires_at": {"type": "string", "format": "date-time"},
        "inputs": {"type": "object"}
      },
      "required": ["proposal_id", "sku", "current_price", "proposed_price", "expected_margin", "confidence"]
    }
  },
  "required": ["ok", "proposal"]
}
```
Notes:
- Internally, the optimizer returns keys like `recommended_price` and `rationale`; the MCP wrapper maps these into the `proposal` shape above and supplies defaults when optimizer keys are absent.

### explain_proposal
Purpose: Explain the reasoning behind a proposal.
Input:
```json
{
  "type": "object",
  "properties": {
    "proposal_id": {"type": "string", "minLength": 1},
    "capability_token": {"type": "string"}
  },
  "required": ["proposal_id", "capability_token"],
  "additionalProperties": false
}
```
Output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "explanation": {
      "type": "object",
      "properties": {
        "proposal_id": {"type": "string"},
        "reasoning": {"type": "string"},
        "factors": {"type": "array"},
        "algorithm": {"type": "string"},
        "generated_at": {"type": "string", "format": "date-time"}
      },
      "required": ["proposal_id", "reasoning"]
    }
  },
  "required": ["ok", "explanation"]
}
```

### apply_proposal
Purpose: Apply an approved proposal.
Input:
```json
{
  "type": "object",
  "properties": {
    "proposal_id": {"type": "string", "minLength": 1},
    "capability_token": {"type": "string"}
  },
  "required": ["proposal_id", "capability_token"],
  "additionalProperties": false
}
```
Output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "result": {
      "type": "object",
      "properties": {
        "proposal_id": {"type": "string"},
        "status": {"type": "string", "const": "applied"},
        "applied_at": {"type": "string", "format": "date-time"},
        "message": {"type": "string"}
      },
      "required": ["proposal_id", "status"]
    }
  },
  "required": ["ok", "result"]
}
```

### cancel_proposal
Purpose: Cancel a pending proposal.
Input:
```json
{
  "type": "object",
  "properties": {
    "proposal_id": {"type": "string", "minLength": 1},
    "capability_token": {"type": "string"}
  },
  "required": ["proposal_id", "capability_token"],
  "additionalProperties": false
}
```
Output:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "result": {
      "type": "object",
      "properties": {
        "proposal_id": {"type": "string"},
        "status": {"type": "string", "const": "cancelled"},
        "cancelled_at": {"type": "string", "format": "date-time"},
        "message": {"type": "string"}
      },
      "required": ["proposal_id", "status"]
    }
  },
  "required": ["ok", "result"]
}
```

### optimize_price (legacy)
Purpose: Backward-compatible wrapper that forwards to `propose_price`.
Input:
```json
{
  "type": "object",
  "properties": {
    "payload": {"type": "object"},
    "capability_token": {"type": "string"}
  },
  "required": ["payload", "capability_token"],
  "additionalProperties": false
}
```
Output: Same as `propose_price` output on success; on errors may return `{ ok: false, error: "legacy_call_error", message: "..." }`.

### auth_metrics
Purpose: Return authentication metrics (admin scope required).
Input/Output: Same shape as Data Collector `auth_metrics`, with `service` set to `price-optimizer`.

---

## Authentication Field

For tools that require authorization, the following field is used:
```json
{
  "type": "object",
  "properties": {
    "capability_token": {"type": "string", "minLength": 1}
  },
  "required": ["capability_token"]
}
```

Embed this field in the tool input schema where applicable (as shown above). Tools without authentication needs omit it.

## Notes on Future Alignment

- If you prefer a nested `features` object for `fetch_market_features`, update the server to wrap repository results accordingly; until then, clients should accept the flat shape documented here.
- `start_collection` currently supports only the `mock` connector; extend both code and this document when additional connectors are implemented.
- The optimizer wrapper supplies defaults (`confidence`, `reasoning`, `expected_margin`) when the core optimizer omits those fields; harmonize naming if/when the core optimizer’s return keys change.
