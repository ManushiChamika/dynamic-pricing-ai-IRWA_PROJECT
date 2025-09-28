#!/usr/bin/env python3
"""
Unit tests for LLMBrain AI-only tool selection.
Tests the decide_tool method with mocked LLM responses.
"""

import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to Python path
HERE = Path(__file__).resolve()
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from core.agents.pricing_optimizer import LLMBrain


def test_valid_ai_selection():
    """Test successful AI tool selection with valid LLM response"""
    print("Testing valid AI selection...")
    
    # Mock LLM client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"tool_name": "rule_based", "arguments": {}, "reason": "Conservative approach for stable pricing"}'
    mock_client.chat.completions.create.return_value = mock_response
    
    # Create optimizer with mocked client
    optimizer = LLMBrain()
    optimizer.client = mock_client
    
    # Test tool selection
    available_tools = {"rule_based": lambda x: 100.0, "ml_model": lambda x: 110.0}
    market_context = {"record_count": 5, "latest_price": 95.0}
    
    result = optimizer.decide_tool("optimize laptop pricing", available_tools, market_context)
    
    # Verify result
    assert result["tool_name"] == "rule_based"
    assert result["reason"] == "Conservative approach for stable pricing"
    assert "error" not in result
    print("PASS: Valid AI selection test passed")


def test_invalid_tool_name():
    """Test AI selection with invalid tool name"""
    print("Testing invalid tool name...")
    
    # Mock LLM client with invalid tool
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"tool_name": "nonexistent_tool", "arguments": {}, "reason": "Invalid choice"}'
    mock_client.chat.completions.create.return_value = mock_response
    
    optimizer = LLMBrain()
    optimizer.client = mock_client
    
    available_tools = {"rule_based": lambda x: 100.0}
    result = optimizer.decide_tool("test request", available_tools, {})
    
    # Verify error handling
    assert result["error"] == "ai_selection_failed"
    assert "Invalid tool_name 'nonexistent_tool'" in result["message"]
    print("PASS: Invalid tool name test passed")


def test_malformed_json():
    """Test AI selection with malformed JSON response"""
    print("Testing malformed JSON...")
    
    # Mock LLM client with invalid JSON
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = 'This is not valid JSON at all'
    mock_client.chat.completions.create.return_value = mock_response
    
    optimizer = LLMBrain()
    optimizer.client = mock_client
    
    available_tools = {"rule_based": lambda x: 100.0}
    result = optimizer.decide_tool("test request", available_tools, {})
    
    # Verify error handling
    assert result["error"] == "ai_selection_failed"
    assert "missing JSON format" in result["message"]
    print("PASS: Malformed JSON test passed")


def test_invalid_json_structure():
    """Test AI selection with invalid JSON structure"""
    print("Testing invalid JSON structure...")
    
    # Mock LLM client with structurally invalid JSON
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"tool_name": "rule_based", "arguments": "not_a_dict"}'
    mock_client.chat.completions.create.return_value = mock_response
    
    optimizer = LLMBrain()
    optimizer.client = mock_client
    
    available_tools = {"rule_based": lambda x: 100.0}
    result = optimizer.decide_tool("test request", available_tools, {})
    
    # Verify error handling
    assert result["error"] == "ai_selection_failed"
    assert "Arguments must be a dictionary" in result["message"]
    print("PASS: Invalid JSON structure test passed")


def test_no_client_strict_mode():
    """Test strict mode with no LLM client"""
    print("Testing strict mode without LLM client...")
    
    # Create optimizer with no client and strict mode
    optimizer = LLMBrain(strict_ai_selection=True)
    # Ensure no client is set
    optimizer.client = None
    
    available_tools = {"rule_based": lambda x: 100.0}
    result = optimizer.decide_tool("test request", available_tools, {})
    
    # Verify error handling
    assert result["error"] == "ai_selection_failed"
    assert "No LLM client available and strict_ai_selection=True" in result["message"]
    print("PASS: No client strict mode test passed")


def test_no_client_fallback_mode():
    """Test fallback mode with no LLM client"""
    print("Testing fallback mode without LLM client...")
    
    # Create optimizer with no client and fallback mode
    optimizer = LLMBrain(strict_ai_selection=False)
    optimizer.client = None
    
    available_tools = {"rule_based": lambda x: 100.0, "profit_maximization": lambda x: 120.0}
    
    # Test profit keyword fallback
    result1 = optimizer.decide_tool("maximize profit for this product", available_tools, {})
    assert result1["tool_name"] == "profit_maximization"
    assert "fallback: keyword 'profit' detected" in result1["reason"]
    
    # Test default fallback
    result2 = optimizer.decide_tool("generic request", available_tools, {})
    assert result2["tool_name"] == "rule_based"
    assert "fallback: default conservative approach" in result2["reason"]
    
    print("PASS: Fallback mode test passed")


def test_llm_request_exception():
    """Test LLM request failure handling"""
    print("Testing LLM request exception...")
    
    # Mock LLM client to raise exception
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API connection failed")
    
    optimizer = LLMBrain()
    optimizer.client = mock_client
    
    available_tools = {"rule_based": lambda x: 100.0}
    result = optimizer.decide_tool("test request", available_tools, {})
    
    # Verify error handling
    assert result["error"] == "ai_selection_failed"
    assert "LLM request failed: API connection failed" in result["message"]
    print("PASS: LLM request exception test passed")


def test_missing_tool_name():
    """Test response missing tool_name field"""
    print("Testing missing tool_name...")
    
    # Mock LLM client with missing tool_name
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"arguments": {}, "reason": "Missing tool name"}'
    mock_client.chat.completions.create.return_value = mock_response
    
    optimizer = LLMBrain()
    optimizer.client = mock_client
    
    available_tools = {"rule_based": lambda x: 100.0}
    result = optimizer.decide_tool("test request", available_tools, {})
    
    # Verify error handling
    assert result["error"] == "ai_selection_failed"
    assert "Missing tool_name in LLM response" in result["message"]
    print("PASS: Missing tool_name test passed")


def run_all_tests():
    """Run all unit tests"""
    print("Running LLMBrain AI selection unit tests...\n")
    
    try:
        test_valid_ai_selection()
        test_invalid_tool_name()
        test_malformed_json()
        test_invalid_json_structure()
        test_no_client_strict_mode()
        test_no_client_fallback_mode()
        test_llm_request_exception()
        test_missing_tool_name()
        
        print("\nSUCCESS: All tests passed!")
        return True
        
    except Exception as e:
        print(f"\nFAILED: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)