# LLM Refactoring Testing Guide

## Overview

This guide covers comprehensive testing for the LLM system refactoring that unified provider management, improved error handling, and added multi-provider fallback support.

## Test Files

### 1. `test_llm_comprehensive.py`
**Purpose:** Unit tests for core LLM client functionality

**Test Coverage:**
- **Initialization Tests**
  - No API key scenario
  - Explicit key initialization
  - Environment key initialization
  
- **Chat Completion Tests**
  - Successful chat completion
  - Provider fallback on failure
  - All providers failing scenario
  - Usage tracking verification
  
- **Streaming Tests**
  - Successful streaming
  - Fallback to non-streaming
  - Usage capture in streams
  
- **Tool Calling Tests**
  - No tool calls
  - Single tool call execution
  - Streaming with tool calls
  - Tool result serialization

**Run:** `pytest test_llm_comprehensive.py -v`

### 2. `test_llm_integration.py`
**Purpose:** Integration tests for LLM with other system components

**Test Coverage:**
- **Price Optimizer Integration**
  - LLM brain with available provider
  - Fallback when LLM unavailable
  - Tool selection via LLM
  
- **Chat API Integration**
  - Thread message retrieval
  - Message editing
  - Message deletion
  
- **End-to-End Workflows**
  - Full pricing workflow with LLM
  - Full workflow with fallback
  - Multi-competitor pricing scenarios

**Run:** `pytest test_llm_integration.py -v`

### 3. `test_llm_provider_verification.py`
**Purpose:** Real provider verification (existing test)

**Test Coverage:**
- OpenRouter provider
- OpenAI provider
- Gemini provider
- Provider fallback behavior

**Run:** `pytest test_llm_provider_verification.py -v`

## Running Tests

### Quick Test (All Tests)
```bash
run_llm_tests.bat
```

### Individual Test Suites
```bash
# Comprehensive unit tests
pytest test_llm_comprehensive.py -v -s

# Integration tests
pytest test_llm_integration.py -v -s

# Provider verification
pytest test_llm_provider_verification.py -v -s
```

### Specific Test Classes
```bash
# Test only initialization
pytest test_llm_comprehensive.py::TestLLMClientInitialization -v

# Test only chat functionality
pytest test_llm_comprehensive.py::TestLLMClientChat -v

# Test only streaming
pytest test_llm_comprehensive.py::TestLLMClientStreaming -v
```

### Debug Mode
```bash
# With detailed output
pytest test_llm_comprehensive.py -v -s --tb=long

# Stop on first failure
pytest test_llm_comprehensive.py -x

# Run with coverage
pytest test_llm_comprehensive.py --cov=core.agents.llm_client --cov-report=html
```

## Test Scenarios

### 1. Provider Fallback Testing
**Scenario:** Primary provider fails, system falls back to secondary

**Test Location:** `test_llm_comprehensive.py::TestLLMClientChat::test_chat_provider_fallback`

**Expected Behavior:**
- First provider attempt fails
- Second provider succeeds
- Active provider switches to working one
- Usage is captured correctly

### 2. Strict AI Selection Testing
**Scenario:** LLM unavailable with strict mode enabled

**Test Location:** `test_llm_comprehensive.py::TestLLMBrain::test_llm_brain_unavailable_strict`

**Expected Behavior:**
- Returns error when LLM unavailable
- Does not fall back to heuristics
- Clear error message provided

### 3. Graceful Degradation Testing
**Scenario:** LLM unavailable with fallback enabled

**Test Location:** `test_llm_comprehensive.py::TestLLMBrain::test_llm_brain_unavailable_fallback`

**Expected Behavior:**
- Falls back to keyword-based selection
- Returns valid tool choice
- Indicates fallback in reason

### 4. Tool Calling Integration
**Scenario:** LLM requests tool execution

**Test Location:** `test_llm_comprehensive.py::TestLLMClientToolCalling::test_chat_with_tools_single_call`

**Expected Behavior:**
- Tool call detected
- Function executed
- Result sent back to LLM
- Final response generated
- Tools tracked in usage

### 5. Streaming with Error Recovery
**Scenario:** Streaming fails, falls back to regular chat

**Test Location:** `test_llm_comprehensive.py::TestLLMClientStreaming::test_chat_stream_fallback_to_nonstreaming`

**Expected Behavior:**
- Streaming attempt fails
- Falls back to non-streaming
- Response still delivered
- No error raised to caller

## Mocking Strategy

### OpenAI Client Mocking
```python
mock_openai = Mock()
mock_client = Mock()
mock_response = Mock()
mock_response.choices = [Mock(message=Mock(content="Response"))]
mock_client.chat.completions.create = Mock(return_value=mock_response)
mock_openai.OpenAI = Mock(return_value=mock_client)

with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
    client = LLMClient(api_key="test-key")
```

### Environment Mocking
```python
with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
    client = LLMClient()
```

## Validation Checklist

- [ ] All initialization modes tested
- [ ] Provider fallback tested
- [ ] Streaming tested
- [ ] Tool calling tested
- [ ] Usage tracking verified
- [ ] Error handling validated
- [ ] LLM brain integration tested
- [ ] Price optimizer integration tested
- [ ] Chat API integration tested
- [ ] End-to-end workflows tested

## Performance Benchmarks

Expected test execution times:
- `test_llm_comprehensive.py`: ~5 seconds
- `test_llm_integration.py`: ~10 seconds
- `test_llm_provider_verification.py`: ~3 seconds
- **Total suite:** ~18 seconds

## Debugging Failed Tests

### Common Issues

**Issue:** Test fails with "openai package not installed"
**Solution:** `pip install openai`

**Issue:** Test fails with database errors
**Solution:** Check test database cleanup in teardown methods

**Issue:** Mock not being called
**Solution:** Verify patch target matches actual import path

### Debug Logging
Enable debug logging in tests:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
os.environ["DEBUG_LLM"] = "1"
```

## Continuous Integration

For CI/CD pipelines:
```yaml
- name: Run LLM Tests
  run: |
    pytest test_llm_comprehensive.py test_llm_integration.py -v --tb=short
```

## Manual Testing Scenarios

After automated tests pass, manually verify:

1. **Chat Interface**
   - Start app with valid API key
   - Send message to chat
   - Verify response received
   - Check provider used in logs

2. **Price Optimizer**
   - Run pricing agent
   - Verify tool selection logic
   - Check pricing proposals

3. **Provider Switching**
   - Start with primary provider
   - Simulate failure (invalid key)
   - Verify fallback occurs
   - Check logs for fallback messages

## Future Enhancements

- Add performance benchmarking tests
- Add memory leak detection tests
- Add concurrent request tests
- Add rate limit handling tests
- Add cost tracking tests
