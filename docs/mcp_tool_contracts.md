# MCP Tool Contracts and JSON Schemas

## Standard Error Response Schema

```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": false},
    "error": {"type": "string"},
    "error_code": {"type": "string", "enum": ["validation_error", "not_found", "unauthorized", "internal_error", "timeout"]},
    "details": {"type": "object"}
  },
  "required": ["ok", "error"],
  "additionalProperties": false
}
```

## Health Tools (All Servers)

### ping
**Purpose**: Basic connectivity test
**Input**: None
**Output**:
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

### health
**Purpose**: Detailed health status
**Input**: None  
**Output**:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean"},
    "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
    "version": {"type": "string"},
    "uptime_seconds": {"type": "number"},
    "dependencies": {
      "type": "object",
      "patternProperties": {
        ".*": {"type": "string", "enum": ["ok", "error", "unknown"]}
      }
    }
  },
  "required": ["ok", "status", "version"]
}
```

### version
**Purpose**: Server version information
**Input**: None
**Output**:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "version": {"type": "string"},
    "build": {"type": "string"},
    "commit": {"type": "string"}
  },
  "required": ["ok", "version"]
}
```

## Data Collector Service Tools

### start_collection
**Purpose**: Start background data collection job
**Input**:
```json
{
  "type": "object",
  "properties": {
    "sku": {"type": "string", "minLength": 1},
    "market": {"type": "string", "default": "DEFAULT"},
    "connector": {"type": "string", "enum": ["mock", "web_scraper"], "default": "mock"},
    "depth": {"type": "integer", "minimum": 1, "maximum": 100, "default": 1}
  },
  "required": ["sku"],
  "additionalProperties": false
}
```
**Output**:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "job_id": {"type": "string"},
    "status": {"type": "string", "const": "started"}
  },
  "required": ["ok", "job_id", "status"]
}
```

### get_job_status  
**Purpose**: Check collection job status
**Input**:
```json
{
  "type": "object",
  "properties": {
    "job_id": {"type": "string", "minLength": 1}
  },
  "required": ["job_id"],
  "additionalProperties": false
}
```
**Output**:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "job": {
      "type": "object",
      "properties": {
        "job_id": {"type": "string"},
        "status": {"type": "string", "enum": ["pending", "running", "done", "failed"]},
        "sku": {"type": "string"},
        "market": {"type": "string"},
        "connector": {"type": "string"},
        "depth": {"type": "integer"},
        "created_at": {"type": "string", "format": "date-time"},
        "completed_at": {"type": ["string", "null"], "format": "date-time"},
        "error": {"type": ["string", "null"]}
      },
      "required": ["job_id", "status", "sku", "market", "connector", "depth", "created_at"]
    }
  },
  "required": ["ok", "job"]
}
```

### fetch_market_features
**Purpose**: Fetch market data features for SKU
**Input**:
```json
{
  "type": "object",
  "properties": {
    "sku": {"type": "string", "minLength": 1},
    "market": {"type": "string", "default": "DEFAULT"},
    "time_window": {"type": "string", "pattern": "^P\\d+D$", "default": "P7D"},
    "freshness_sla_minutes": {"type": "integer", "minimum": 1, "maximum": 1440, "default": 60}
  },
  "required": ["sku"],
  "additionalProperties": false
}
```
**Output**:
```json
{
  "type": "object",
  "properties": {
    "ok": {"type": "boolean", "const": true},
    "features": {
      "type": "object",
      "properties": {
        "sku": {"type": "string"},
        "market": {"type": "string"},
        "our_price": {"type": ["number", "null"]},
        "competitor_price": {"type": ["number", "null"]},
        "demand_index": {"type": ["number", "null"]},
        "cost": {"type": ["number", "null"]},
        "last_updated": {"type": "string", "format": "date-time"}
      },
      "required": ["sku", "market", "last_updated"]
    }
  },
  "required": ["ok", "features"]
}
```

### list_sources
**Purpose**: List available data sources
**Input**: None
**Output**:
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
          "type": {"type": "string", "enum": ["mock", "web_scraper", "api"]},
          "status": {"type": "string", "enum": ["active", "inactive", "error"]},
          "description": {"type": "string"}
        },
        "required": ["name", "type", "status"]
      }
    }
  },
  "required": ["ok", "sources"]
}
```

### import_product_catalog
**Purpose**: Import/update product catalog
**Input**:
```json
{
  "type": "object",
  "properties": {
    "rows": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sku": {"type": "string", "minLength": 1},
          "name": {"type": "string"},
          "category": {"type": "string"},
          "cost": {"type": ["number", "null"]},
          "min_price": {"type": ["number", "null"]},
          "max_price": {"type": ["number", "null"]}
        },
        "required": ["sku"],
        "additionalProperties": true
      }
    }
  },
  "required": ["rows"],
  "additionalProperties": false
}
```

## Alert Service Tools

### list_alerts
**Purpose**: List active alerts with optional filtering
**Input**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string", "enum": ["active", "acknowledged", "resolved"]},
    "rule_id": {"type": "string"},
    "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100}
  },
  "additionalProperties": false
}
```

### create_alert
**Purpose**: Create new alert rule
**Input**:
```json
{
  "type": "object",
  "properties": {
    "spec": {
      "type": "object",
      "properties": {
        "name": {"type": "string", "minLength": 1},
        "condition": {"type": "string"},
        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "enabled": {"type": "boolean", "default": true}
      },
      "required": ["name", "condition", "severity"]
    }
  },
  "required": ["spec"],
  "additionalProperties": false
}
```

### ack_alert / resolve_alert
**Purpose**: Acknowledge or resolve alert
**Input**:
```json
{
  "type": "object",
  "properties": {
    "alert_id": {"type": "string", "minLength": 1}
  },
  "required": ["alert_id"],
  "additionalProperties": false
}
```

## Price Optimizer Service Tools

### propose_price
**Purpose**: Generate price optimization proposal
**Input**:
```json
{
  "type": "object",
  "properties": {
    "sku": {"type": "string", "minLength": 1},
    "our_price": {"type": "number", "minimum": 0},
    "competitor_price": {"type": ["number", "null"], "minimum": 0},
    "demand_index": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
    "cost": {"type": ["number", "null"], "minimum": 0},
    "min_price": {"type": "number", "minimum": 0, "default": 0},
    "max_price": {"type": "number", "minimum": 0},
    "min_margin": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.12}
  },
  "required": ["sku", "our_price", "max_price"],
  "additionalProperties": false
}
```
**Output**:
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
        "expires_at": {"type": "string", "format": "date-time"}
      },
      "required": ["proposal_id", "sku", "current_price", "proposed_price", "expected_margin", "confidence"]
    }
  },
  "required": ["ok", "proposal"]
}
```

### explain_proposal
**Purpose**: Explain optimization reasoning
**Input**:
```json
{
  "type": "object",
  "properties": {
    "proposal_id": {"type": "string", "minLength": 1}
  },
  "required": ["proposal_id"],
  "additionalProperties": false
}
```

### apply_proposal
**Purpose**: Apply approved price proposal
**Input**:
```json
{
  "type": "object",
  "properties": {
    "proposal_id": {"type": "string", "minLength": 1}
  },
  "required": ["proposal_id"],
  "additionalProperties": false
}
```

### cancel_proposal
**Purpose**: Cancel pending proposal
**Input**:
```json
{
  "type": "object",
  "properties": {
    "proposal_id": {"type": "string", "minLength": 1}
  },
  "required": ["proposal_id"],
  "additionalProperties": false
}
```

## Tool Registration Pattern

Each server should register tools with proper validation:

```python
from jsonschema import validate
from typing import Dict, Any

def validate_input(schema: Dict[str, Any]):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                validate(kwargs, schema)
                return await func(*args, **kwargs)
            except Exception as e:
                return {
                    "ok": False,
                    "error": str(e),
                    "error_code": "validation_error"
                }
        return wrapper
    return decorator

@mcp.tool()
@validate_input(START_COLLECTION_SCHEMA)
async def start_collection(**kwargs) -> dict:
    # Implementation here
```

## Authentication Schema

For tools requiring authentication:

```json
{
  "type": "object",
  "properties": {
    "capability_token": {"type": "string", "minLength": 1}
  },
  "required": ["capability_token"]
}
```