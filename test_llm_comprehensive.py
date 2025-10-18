import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agents.llm_client import LLMClient, get_llm_client
from core.agents.price_optimizer.llm_brain import LLMBrain


class TestLLMClientInitialization:
    
    def test_no_api_key_initialization(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "", "OPENAI_API_KEY": "", "GEMINI_API_KEY": ""}, clear=True):
            with patch("core.agents.llm_client.importlib.import_module"):
                client = LLMClient()
                assert not client.is_available()
                assert client.unavailable_reason() == "no API key configured"
    
    def test_explicit_key_initialization(self):
        mock_openai = Mock()
        mock_openai.OpenAI = Mock(return_value=Mock())
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            client = LLMClient(api_key="test-key", model="gpt-4o-mini")
            assert client.is_available()
            assert client.model == "gpt-4o-mini"
    
    def test_env_key_initialization(self):
        mock_openai = Mock()
        mock_openai.OpenAI = Mock(return_value=Mock())
        
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-or-key"}, clear=True):
            with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
                client = LLMClient()
                assert client.is_available()
                assert client.provider() == "openrouter"


class TestLLMClientChat:
    
    def test_chat_success(self):
        mock_openai = Mock()
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        mock_openai.OpenAI = Mock(return_value=mock_client)
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            client = LLMClient(api_key="test-key")
            result = client.chat([{"role": "user", "content": "Hello"}])
            
            assert result == "Test response"
            assert client.last_usage["prompt_tokens"] == 10
            assert client.last_usage["completion_tokens"] == 5
    
    def test_chat_provider_fallback(self):
        mock_openai = Mock()
        
        failing_client = Mock()
        failing_client.chat.completions.create = Mock(side_effect=Exception("Provider 1 failed"))
        
        working_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Fallback response"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        working_client.chat.completions.create = Mock(return_value=mock_response)
        
        call_count = [0]
        def mock_openai_init(**kwargs):
            call_count[0] += 1
            return failing_client if call_count[0] == 1 else working_client
        
        mock_openai.OpenAI = Mock(side_effect=mock_openai_init)
        
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "key1", "OPENAI_API_KEY": "key2"}, clear=True):
            with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
                client = LLMClient()
                result = client.chat([{"role": "user", "content": "Hello"}])
                
                assert result == "Fallback response"
    
    def test_chat_all_providers_fail(self):
        mock_openai = Mock()
        mock_client = Mock()
        mock_client.chat.completions.create = Mock(side_effect=Exception("All failed"))
        mock_openai.OpenAI = Mock(return_value=mock_client)
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            client = LLMClient(api_key="test-key")
            
            with pytest.raises(RuntimeError, match="All LLM providers failed"):
                client.chat([{"role": "user", "content": "Hello"}])


class TestLLMClientStreaming:
    
    def test_chat_stream_success(self):
        mock_openai = Mock()
        mock_client = Mock()
        
        mock_events = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))], usage=None),
            Mock(choices=[Mock(delta=Mock(content=" world"))], usage=None),
            Mock(choices=[], usage=Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15))
        ]
        
        mock_client.chat.completions.create = Mock(return_value=iter(mock_events))
        mock_openai.OpenAI = Mock(return_value=mock_client)
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            client = LLMClient(api_key="test-key")
            
            chunks = list(client.chat_stream([{"role": "user", "content": "Hello"}]))
            
            assert chunks == ["Hello", " world"]
            assert client.last_usage["prompt_tokens"] == 10
    
    def test_chat_stream_fallback_to_nonstreaming(self):
        mock_openai = Mock()
        mock_client = Mock()
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Fallback response"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        def mock_create(**kwargs):
            if kwargs.get("stream"):
                raise Exception("Streaming not supported")
            return mock_response
        
        mock_client.chat.completions.create = Mock(side_effect=mock_create)
        mock_openai.OpenAI = Mock(return_value=mock_client)
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            client = LLMClient(api_key="test-key")
            
            chunks = list(client.chat_stream([{"role": "user", "content": "Hello"}]))
            
            assert chunks == ["Fallback response"]


class TestLLMClientToolCalling:
    
    def test_chat_with_tools_no_calls(self):
        mock_openai = Mock()
        mock_client = Mock()
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response", tool_calls=None))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        mock_openai.OpenAI = Mock(return_value=mock_client)
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            client = LLMClient(api_key="test-key")
            
            result = client.chat_with_tools(
                messages=[{"role": "user", "content": "Hello"}],
                tools=[],
                functions_map={}
            )
            
            assert result == "Response"
    
    def test_chat_with_tools_single_call(self):
        mock_openai = Mock()
        mock_client = Mock()
        
        tool_call = Mock()
        tool_call.id = "call_123"
        tool_call.type = "function"
        tool_call.function = Mock()
        tool_call.function.name = "get_price"
        tool_call.function.arguments = '{"product":"laptop"}'
        
        first_response = Mock()
        first_response.choices = [Mock(message=Mock(content=None, tool_calls=[tool_call]))]
        first_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        
        second_response = Mock()
        second_response.choices = [Mock(message=Mock(content="Price is $1000", tool_calls=None))]
        second_response.usage = Mock(prompt_tokens=20, completion_tokens=10, total_tokens=30)
        
        mock_client.chat.completions.create = Mock(side_effect=[first_response, second_response])
        mock_openai.OpenAI = Mock(return_value=mock_client)
        
        def mock_get_price(product):
            return {"price": 1000}
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            client = LLMClient(api_key="test-key")
            
            result = client.chat_with_tools(
                messages=[{"role": "user", "content": "Get laptop price"}],
                tools=[{"type": "function", "function": {"name": "get_price"}}],
                functions_map={"get_price": mock_get_price}
            )
            
            assert result == "Price is $1000"
            assert client.last_usage["tools_used"] == ["get_price"]
    
    def test_chat_with_tools_stream_no_calls(self):
        mock_openai = Mock()
        mock_client = Mock()
        
        mock_events = [
            Mock(choices=[Mock(delta=Mock(content="Hello", tool_calls=None))], usage=None),
            Mock(choices=[Mock(delta=Mock(content=" world", tool_calls=None))], usage=None),
            Mock(choices=[], usage=Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15))
        ]
        
        mock_client.chat.completions.create = Mock(return_value=iter(mock_events))
        mock_openai.OpenAI = Mock(return_value=mock_client)
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            client = LLMClient(api_key="test-key")
            
            events = list(client.chat_with_tools_stream(
                messages=[{"role": "user", "content": "Hello"}],
                tools=[],
                functions_map={}
            ))
            
            text_deltas = [e["text"] for e in events if e.get("type") == "delta"]
            assert text_deltas == ["Hello", " world"]


class TestLLMBrain:
    
    def test_llm_brain_available(self):
        mock_openai = Mock()
        mock_openai.OpenAI = Mock(return_value=Mock())
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            brain = LLMBrain(api_key="test-key")
            assert brain.llm_client.is_available()
    
    def test_llm_brain_unavailable_strict(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "", "OPENAI_API_KEY": "", "GEMINI_API_KEY": ""}, clear=True):
            with patch("core.agents.llm_client.importlib.import_module"):
                brain = LLMBrain(strict_ai_selection=True)
                assert not brain.llm_client.is_available()
                
                result = brain.decide_tool(
                    "maximize profit",
                    {"rule_based": lambda: None, "profit_maximization": lambda: None}
                )
                
                assert result.get("error") == "ai_selection_failed"
    
    def test_llm_brain_unavailable_fallback(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "", "OPENAI_API_KEY": "", "GEMINI_API_KEY": ""}, clear=True):
            with patch("core.agents.llm_client.importlib.import_module"):
                brain = LLMBrain(strict_ai_selection=False)
                assert not brain.llm_client.is_available()
                
                result = brain.decide_tool(
                    "maximize profit",
                    {"rule_based": lambda: None, "profit_maximization": lambda: None}
                )
                
                assert result.get("tool_name") == "profit_maximization"
                assert "fallback" in result.get("reason", "")
    
    def test_llm_brain_tool_selection(self):
        mock_openai = Mock()
        mock_client = Mock()
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"tool_name": "profit_maximization", "arguments": {}, "reason": "User wants to maximize profit"}'))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=30, total_tokens=130)
        
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        mock_openai.OpenAI = Mock(return_value=mock_client)
        
        with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
            brain = LLMBrain(api_key="test-key")
            
            result = brain.decide_tool(
                "maximize profit",
                {"rule_based": lambda: None, "profit_maximization": lambda: None}
            )
            
            assert result.get("tool_name") == "profit_maximization"
            assert "reason" in result
            assert result.get("error") is None


class TestGetLLMClient:
    
    def test_singleton_cache(self):
        mock_openai = Mock()
        mock_openai.OpenAI = Mock(return_value=Mock())
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
                import core.agents.llm_client
                core.agents.llm_client._llm_client_cache = None
                
                client1 = get_llm_client()
                client2 = get_llm_client()
                
                assert client1 is client2
    
    def test_custom_model_fresh_instance(self):
        mock_openai = Mock()
        mock_openai.OpenAI = Mock(return_value=Mock())
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch("core.agents.llm_client.importlib.import_module", return_value=mock_openai):
                import core.agents.llm_client
                core.agents.llm_client._llm_client_cache = None
                
                client1 = get_llm_client()
                client2 = get_llm_client(model="gpt-4")
                
                assert client1 is not client2
                assert client2.model == "gpt-4"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
