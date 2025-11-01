# Price Optimizer Agent

## Overview

The Price Optimizer Agent uses AI-powered tool selection to intelligently choose the most appropriate pricing algorithm based on user intent and market context. This agent has been refactored to use **AI-only decision making**, eliminating hard-coded heuristics in favor of intelligent LLM-based selection.

## Key Features

- **AI-Only Tool Selection**: Uses LLM to choose between pricing algorithms based on context
- **Market-Aware Decisions**: Incorporates real market data (record count, prices) into decision making
- **Strict Error Handling**: Clear failure modes with detailed error messages
- **Comprehensive Telemetry**: Logs all AI decisions for transparency and debugging
- **Backward Compatibility**: Optional fallback mode for legacy behavior

## Architecture

The system consists of two main classes:

### LLMBrain
The core AI decision-making engine that:
- Takes user requests and market context as input
- Uses OpenRouter API to query LLMs for tool selection
- Validates LLM responses against available tools
- Returns structured decisions with reasoning

### Workflow Integration
The `process_full_workflow` method orchestrates the complete pricing pipeline:
1. Check data freshness and request updates if needed
2. Build market context from available data
3. Use AI to select the optimal pricing algorithm
4. Execute the selected algorithm and return results

## Configuration

### Environment Variables

```bash
# Required for AI functionality
OPENROUTER_API_KEY=your_api_key_here

# Optional configuration
STRICT_AI_SELECTION=true  # Default: true (fail if no LLM client)
```

### Constructor Options

```python
from core.agents.pricing_optimizer import LLMBrain

# Strict mode (default) - fails if no LLM client available
brain = LLMBrain(
    api_key="your-key",
    model="anthropic/claude-3-haiku-20240307",  # Default model
    base_url="https://openrouter.ai/api/v1",    # Default endpoint
    strict_ai_selection=True                     # Default: True
)

# Fallback mode - uses keyword heuristics if no LLM client
brain = LLMBrain(strict_ai_selection=False)
```

## AI Tool Selection Process

### Available Pricing Algorithms

The AI can choose from three pricing algorithms:

1. **`rule_based`** - Conservative approach using predefined rules
   - Best for: Stable markets, risk-averse pricing
   - Use cases: New products, uncertain market conditions

2. **`ml_model`** - Machine learning-based predictions
   - Best for: Historical data analysis, pattern recognition
   - Use cases: Established products with rich data

3. **`profit_maximization`** - Aggressive profit optimization
   - Best for: Competitive markets, revenue focus
   - Use cases: High-demand products, market leadership

### Decision Context

The AI receives the following context for decision making:

```json
{
  "user_request": "optimize pricing for Dell laptop",
  "market_context": {
    "record_count": 15,
    "latest_price": 899.99,
    "avg_price": 925.50
  },
  "available_tools": ["rule_based", "ml_model", "profit_maximization"]
}
```

### Expected Response Format

The LLM must respond with valid JSON:

```json
{
  "tool_name": "ml_model",
  "arguments": {},
  "reason": "Sufficient historical data available for ML predictions"
}
```

## Error Handling

### AI Selection Failures

When AI selection fails, the system returns structured error responses:

```json
{
  "error": "ai_selection_failed",
  "message": "Invalid tool_name 'nonexistent_tool', available: ['rule_based', 'ml_model', 'profit_maximization']"
}
```

### Common Failure Modes

1. **No LLM Client** (strict mode): `"No LLM client available and strict_ai_selection=True"`
2. **Malformed JSON**: `"LLM response missing JSON format"`
3. **Invalid Tool**: `"Invalid tool_name 'xyz', available: [...]"`
4. **Missing Fields**: `"Missing tool_name in LLM response"`
5. **API Failure**: `"LLM request failed: Connection timeout"`

### Fallback Behavior

When `strict_ai_selection=False`, the system uses keyword-based fallbacks:

- Requests containing "profit" or "maximize" → `profit_maximization`
- All other requests → `rule_based` (conservative default)

## Telemetry and Logging

### Activity Log Integration

All AI decisions are logged to the activity system:

```python
# Successful AI selection
activity_log.log("llm_brain", "decide_tool.success", "completed", 
    message="selected=ml_model reason='Sufficient data for ML'",
    details={
        "tool_name": "ml_model", 
        "market_context": {...},
        "reason": "Sufficient data for ML predictions"
    }
)

# Failed AI selection
activity_log.log("llm_brain", "decide_tool.failed", "failed",
    message="AI selection failed: Invalid JSON from LLM",
    details={"error": "...", "model": "claude-3-haiku"}
)
```

### Raw Response Logging

LLM responses are logged (truncated for safety):

```python
activity_log.log("llm_brain", "decide_tool.request", "info",
    message="model=claude-3-haiku prompt_len=1240 response_len=87",
    details={
        "raw_response_preview": "{'tool_name': 'ml_model', 'arguments': {}, 'reason': 'Sufficient...",
        "available_tools": ["rule_based", "ml_model", "profit_maximization"]
    }
)
```

## Usage Examples

### Basic Usage

```python
import asyncio
from core.agents.pricing_optimizer import LLMBrain

async def optimize_pricing():
    brain = LLMBrain(api_key="your-openrouter-key")
    
    result = await brain.process_full_workflow(
        user_request="optimize pricing for gaming laptop to maximize profit",
        product_name="Dell XPS Gaming Laptop",
        db_path="data/market.db"
    )
    
    if result.get("status") == "error":
        print(f"Error: {result['message']}")
    else:
        print(f"Optimized price: ${result['price']}")

asyncio.run(optimize_pricing())
```

### Manual Tool Selection

```python
brain = LLMBrain(api_key="your-key")

# Define available pricing tools
tools = {
    "rule_based": rule_based_pricing,
    "ml_model": ml_based_pricing,
    "profit_maximization": profit_maximization_pricing
}

market_context = {
    "record_count": 20,
    "latest_price": 1299.99,
    "avg_price": 1250.00
}

# Get AI recommendation
decision = brain.decide_tool(
    user_intent="competitive pricing for enterprise market",
    available_tools=tools,
    market_context=market_context
)

if "error" in decision:
    print(f"AI selection failed: {decision['message']}")
else:
    selected_tool = decision["tool_name"]
    reasoning = decision["reason"]
    print(f"AI selected: {selected_tool} - {reasoning}")
```

## Testing

Comprehensive unit tests are available in `test_pricing_optimizer_ai.py`:

```bash
python test_pricing_optimizer_ai.py
```

Test coverage includes:
- Valid AI selections with proper JSON responses
- Invalid tool names and malformed JSON handling
- Missing LLM client scenarios (strict vs fallback modes)
- API failure simulation
- Edge cases (missing fields, invalid response structure)

## Migration from Legacy System

### Key Changes from Previous Version

1. **Removed Hard-coded Heuristics**: No more keyword-based tool selection
2. **AI-First Approach**: LLM makes all tool selection decisions
3. **Enhanced Context**: Market data now influences algorithm selection
4. **Strict Error Handling**: Clear failure modes replace silent fallbacks
5. **Improved Telemetry**: Detailed logging of AI decision process

### Backward Compatibility

For systems that cannot use LLM-based selection immediately:

```python
# Enable legacy fallback mode
brain = LLMBrain(strict_ai_selection=False)
```

This preserves the old keyword-based selection when no LLM client is available.

## Best Practices

### API Key Management
- Store API keys in environment variables, never in code
- Use different keys for development/production environments
- Monitor API usage and costs through OpenRouter dashboard

### Prompt Engineering
- The system uses carefully crafted prompts for reliable tool selection
- Prompts include tool descriptions, market context, and strict output formatting
- JSON schema validation ensures consistent LLM responses

### Error Handling
- Always check for `"error"` key in responses
- Log AI selection failures for debugging
- Have fallback strategies for critical pricing scenarios

### Performance Optimization
- Cache LLM responses when appropriate
- Use faster models (e.g., Claude Haiku) for tool selection
- Monitor API latency and adjust timeout settings

## Troubleshooting

### Common Issues

**"No LLM client available"**
- Ensure `OPENROUTER_API_KEY` is set in environment
- Check API key validity and account credits
- Verify network connectivity to OpenRouter API

**"Invalid JSON from LLM"**
- Check OpenRouter service status
- Try different model (some models follow instructions better)
- Review prompt formatting if using custom prompts

**"Invalid tool_name"**
- Verify available tools are correctly defined
- Check for typos in tool names
- Ensure tools dictionary is passed correctly

### Debug Mode

Enable verbose logging to debug AI selection issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show all LLM request/response details
brain = LLMBrain(api_key="your-key")
```