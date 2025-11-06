# Price Optimizer and Data Collector Integration

## Overview

The Price Optimization Agent now **automatically integrates with the Data Collector Agent** to ensure fresh market data before making pricing decisions. This creates an intelligent, self-healing pricing workflow.

## Architecture Flow

```
User Interaction Agent
         ↓
    (requests price optimization)
         ↓
Price Optimization Agent
         ↓
    [1] Check market data freshness
         ↓
    [2] Is data stale/missing?
         ├─ YES → Trigger Data Collector Agent
         │         ↓
         │    (wait for collection)
         │         ↓
         └─ NO  → Continue with optimization
                   ↓
              [3] Get market intelligence
                   ↓
              [4] Run pricing algorithm
                   ↓
              [5] Validate price
                   ↓
              [6] Publish price proposal
```

## Key Changes

### 1. **New Tools in Price Optimizer**

Two new tools have been added to `core/agents/price_optimizer/tools.py`:

#### `check_market_data_freshness(sku: str)`
- Checks if market data exists for a product
- Returns staleness information (minutes since last update)
- Checks both `market_ticks` and `market_data` tables

**Returns:**
```python
{
    "ok": True,
    "sku": "ASUS-ProArt-4910S",
    "product_title": "ASUS ProArt 4910S",
    "has_data": False,
    "last_update": None,
    "minutes_stale": None,
    "is_stale": True,  # True if data is missing or older than 60 minutes
    "market_data_count": 0
}
```

#### `start_market_data_collection(sku: str)`
- Triggers market data collection by publishing to the event bus
- Automatically selects the appropriate connector:
  - `web_scraper` if product has a `source_url`
  - `mock` if no source URL (generates synthetic data for testing)
- Publishes a `MARKET_FETCH_REQUEST` event

**Returns:**
```python
{
    "ok": True,
    "request_id": "5e7cebb2a1be4350a63f7fc8de330ec4",
    "sku": "ASUS-ProArt-4910S",
    "connector": "mock",
    "has_source_url": False,
    "message": "Market data collection started..."
}
```

### 2. **Updated SYSTEM_PROMPT**

The Price Optimization Agent's system prompt now includes the data collection workflow:

```
When handling optimization requests:
1. ALWAYS start by calling get_product_info() to fetch current product data
2. Call check_market_data_freshness() to verify if market data exists and is fresh
3. If market data is missing or stale (older than 60 minutes):
   - Call start_market_data_collection() to trigger data gathering
   - Wait briefly (30 seconds) for data collection to complete
   - Proceed with optimization using available data
4. Call get_market_intelligence() to gather competitive context
5. Analyze the user request and market data to select the appropriate pricing algorithm
...
```

### 3. **Event-Driven Communication**

The integration uses the event bus to communicate between agents:

```python
# Price Optimizer publishes:
Topic.MARKET_FETCH_REQUEST -> {
    "request_id": "...",
    "sku": "ASUS-ProArt-4910S",
    "market": "DEFAULT",
    "sources": ["mock"],
    "depth": 5,
    "horizon_minutes": 60
}

# Data Collector responds by:
# 1. Scraping/collecting market data
# 2. Storing in market_ticks table
# 3. Making data available for optimization
```

## Benefits

### 1. **Self-Healing Pricing**
The system automatically detects missing or stale market data and triggers collection without manual intervention.

### 2. **Always-Fresh Data**
Price optimization decisions are now based on the freshest available market intelligence.

### 3. **Transparent Workflow**
The LLM-powered agent explains its reasoning:
- "Market data is stale, triggering collection..."
- "Data collection started with request ID xyz..."
- "Proceeding with optimization using fresh data..."

### 4. **Graceful Degradation**
If market data collection fails, the optimizer can still proceed with:
- Historical data (if available)
- Rule-based fallback algorithms
- Conservative pricing strategies

## Testing

Run the integration test:

```bash
python test_price_optimizer_integration.py
```

**Expected Output:**
```
============================================================
Testing Price Optimizer Integration for ASUS-ProArt-4910S
============================================================

Step 1: Checking market data freshness...
⚠️  Market data is stale!
   Last update: None
   Minutes stale: N/A
   Market data count: 0

Step 2: Triggering market data collection...
✓ Market data collection started!
   Request ID: 5e7cebb2a1be4350a63f7fc8de330ec4
   Connector: mock
   Has source URL: False

Step 3: Getting product information...
Step 4: Getting market intelligence...
Step 5: Running pricing algorithm...
✓ Price optimization completed!
   Current price: LKR 239051.00
   Recommended price: LKR 239051.00
   Confidence: 80.00%
   Rationale: No change
============================================================
```

## Usage Example

From the user's perspective, the workflow is **completely transparent**:

```
User: "Optimize price for ASUS-ProArt-4910S"
      ↓
System: (automatically checks data freshness)
        (triggers data collection if needed)
        (performs optimization)
        (returns result)
      ↓
User: Receives optimized price with confidence score
```

The user doesn't need to manually check for stale data or trigger collection - the system handles it autonomously!

## Configuration

### Data Freshness Threshold
Currently set to **60 minutes**. Data older than this is considered stale.

```python
is_stale = (minutes_stale > 60)
```

### Collection Wait Time
The LLM agent waits **30 seconds** after triggering collection to allow data to arrive before proceeding with optimization.

```python
# In SYSTEM_PROMPT:
"Wait briefly (30 seconds) for data collection to complete"
```

## Future Enhancements

1. **Parallel Collection**: Trigger collection for multiple related products simultaneously
2. **Smart Wait Times**: Adjust wait time based on connector type (web scraping takes longer than mock data)
3. **Collection Status Tracking**: Poll collection job status instead of fixed wait
4. **Cache Invalidation**: Automatically invalidate and refresh data when external market conditions change
5. **Confidence Scoring**: Adjust optimization confidence based on data freshness and completeness

## Related Files

- `core/agents/price_optimizer/agent.py` - Main agent with updated workflow
- `core/agents/price_optimizer/tools.py` - New data collection tools
- `core/agents/data_collector/agent.py` - Data collection agent
- `core/agents/data_collector/tools.py` - Data collection tools
- `test_price_optimizer_integration.py` - Integration test script

## Event Bus Topics

- `OPTIMIZATION_REQUEST` - Triggers price optimization
- `MARKET_FETCH_REQUEST` - Triggers data collection
- `PRICE_PROPOSAL` - Published after successful optimization
- `ALERT` - System status notifications
