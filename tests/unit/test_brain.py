"""
Tests for brain module (LLM caller).
Tests OpenRouter integration, tool call parsing, error handling, and observability.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, List


class TestBasicLLMCalls:
    """Tests for basic LLM call functionality."""

    def test_create_brain_client(self):
        """Test creating a Brain client with API key."""
        from core.brain import Brain

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            assert brain is not None
            assert brain.api_key == 'test_key'

    def test_brain_requires_api_key(self):
        """Test that Brain raises error without API key."""
        from core.brain import Brain

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                Brain()

    @patch('core.brain.OpenAI')
    def test_simple_completion_call(self, mock_openai):
        """Test making a simple completion call."""
        from core.brain import Brain

        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 8
        mock_response.usage.total_tokens = 18

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="anthropic/claude-3.5-sonnet"
            )

        assert response["content"] == "Hello! How can I help you?"
        assert response["model"] == "anthropic/claude-3.5-sonnet"
        assert response["usage"]["prompt_tokens"] == 10
        assert response["usage"]["completion_tokens"] == 8

    @patch('core.brain.OpenAI')
    def test_completion_with_system_message(self, mock_openai):
        """Test completion with system and user messages."""
        from core.brain import Brain

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I am a helpful assistant."
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 20
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 30

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Who are you?"}
                ],
                model="anthropic/claude-3.5-sonnet"
            )

        # Verify messages were passed correctly
        call_args = mock_client.chat.completions.create.call_args
        assert len(call_args.kwargs['messages']) == 2
        assert call_args.kwargs['messages'][0]['role'] == 'system'
        assert call_args.kwargs['messages'][1]['role'] == 'user'


class TestToolCallParsing:
    """Tests for parsing and handling tool calls."""

    @patch('core.brain.OpenAI')
    def test_parse_tool_calls_from_response(self, mock_openai):
        """Test parsing tool calls from LLM response."""
        from core.brain import Brain

        # Mock tool call response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        # Create mock tool call
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "web_search"
        mock_tool_call.function.arguments = '{"query": "latest AI news"}'

        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 12
        mock_response.usage.total_tokens = 27

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[{"role": "user", "content": "Search for latest AI news"}],
                model="anthropic/claude-3.5-sonnet",
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            }
                        }
                    }
                }]
            )

        assert response["tool_calls"] is not None
        assert len(response["tool_calls"]) == 1
        assert response["tool_calls"][0]["id"] == "call_123"
        assert response["tool_calls"][0]["name"] == "web_search"
        assert response["tool_calls"][0]["arguments"] == {"query": "latest AI news"}

    @patch('core.brain.OpenAI')
    def test_multiple_tool_calls(self, mock_openai):
        """Test parsing multiple tool calls in one response."""
        from core.brain import Brain

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        # Create multiple tool calls
        mock_tool_call_1 = MagicMock()
        mock_tool_call_1.id = "call_1"
        mock_tool_call_1.function.name = "get_weather"
        mock_tool_call_1.function.arguments = '{"location": "San Francisco"}'

        mock_tool_call_2 = MagicMock()
        mock_tool_call_2.id = "call_2"
        mock_tool_call_2.function.name = "get_weather"
        mock_tool_call_2.function.arguments = '{"location": "New York"}'

        mock_response.choices[0].message.tool_calls = [mock_tool_call_1, mock_tool_call_2]
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 20
        mock_response.usage.completion_tokens = 15
        mock_response.usage.total_tokens = 35

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[{"role": "user", "content": "What's the weather in SF and NY?"}],
                model="anthropic/claude-3.5-sonnet"
            )

        assert len(response["tool_calls"]) == 2
        assert response["tool_calls"][0]["name"] == "get_weather"
        assert response["tool_calls"][1]["name"] == "get_weather"


class TestErrorHandling:
    """Tests for error handling and retries."""

    @patch('core.brain.OpenAI')
    def test_retry_on_rate_limit(self, mock_openai):
        """Test that Brain retries on rate limit errors."""
        from core.brain import Brain
        import openai

        mock_client = MagicMock()

        # First call fails with rate limit, second succeeds
        mock_success_response = MagicMock()
        mock_success_response.choices = [MagicMock()]
        mock_success_response.choices[0].message.content = "Success after retry"
        mock_success_response.choices[0].message.tool_calls = None
        mock_success_response.model = "anthropic/claude-3.5-sonnet"
        mock_success_response.usage.prompt_tokens = 10
        mock_success_response.usage.completion_tokens = 5
        mock_success_response.usage.total_tokens = 15

        # Create a proper mock for the RateLimitError
        mock_http_response = MagicMock()
        mock_http_response.request = MagicMock()
        rate_limit_error = openai.RateLimitError(
            "Rate limit exceeded",
            response=mock_http_response,
            body=None
        )

        mock_client.chat.completions.create.side_effect = [
            rate_limit_error,
            mock_success_response
        ]
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain(max_retries=2)
            response = brain.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="anthropic/claude-3.5-sonnet"
            )

        assert response["content"] == "Success after retry"
        assert mock_client.chat.completions.create.call_count == 2

    @patch('core.brain.OpenAI')
    def test_retry_on_api_error(self, mock_openai):
        """Test retry on generic API errors."""
        from core.brain import Brain
        import openai

        mock_client = MagicMock()

        # First call fails, second succeeds
        mock_success_response = MagicMock()
        mock_success_response.choices = [MagicMock()]
        mock_success_response.choices[0].message.content = "Success"
        mock_success_response.choices[0].message.tool_calls = None
        mock_success_response.model = "anthropic/claude-3.5-sonnet"
        mock_success_response.usage.prompt_tokens = 10
        mock_success_response.usage.completion_tokens = 5
        mock_success_response.usage.total_tokens = 15

        # Create a proper mock for the APIError
        mock_http_request = MagicMock()
        api_error = openai.APIError(
            "API temporarily unavailable",
            request=mock_http_request,
            body=None
        )

        mock_client.chat.completions.create.side_effect = [
            api_error,
            mock_success_response
        ]
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain(max_retries=2)
            response = brain.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="anthropic/claude-3.5-sonnet"
            )

        assert response["content"] == "Success"

    @patch('core.brain.OpenAI')
    def test_max_retries_exceeded(self, mock_openai):
        """Test that error is raised when max retries exceeded."""
        from core.brain import Brain, BrainError
        import openai

        mock_client = MagicMock()

        # Create a proper mock for the RateLimitError
        mock_http_response = MagicMock()
        mock_http_response.request = MagicMock()
        rate_limit_error = openai.RateLimitError(
            "Rate limit exceeded",
            response=mock_http_response,
            body=None
        )

        mock_client.chat.completions.create.side_effect = rate_limit_error
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain(max_retries=2)

            with pytest.raises(BrainError, match="Max retries"):
                brain.complete(
                    messages=[{"role": "user", "content": "Hello"}],
                    model="anthropic/claude-3.5-sonnet"
                )

    @patch('core.brain.OpenAI')
    def test_invalid_tool_call_json_handling(self, mock_openai):
        """Test handling of malformed JSON in tool call arguments."""
        from core.brain import Brain

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        # Tool call with invalid JSON
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "web_search"
        mock_tool_call.function.arguments = "{invalid json"

        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[{"role": "user", "content": "Search"}],
                model="anthropic/claude-3.5-sonnet"
            )

        # Should handle gracefully - include error in response
        assert "error" in response["tool_calls"][0]


class TestObservabilityIntegration:
    """Tests for Langfuse observability integration."""

    @patch('core.brain.OpenAI')
    @patch('core.brain.observability')
    def test_generation_tracking(self, mock_observability, mock_openai):
        """Test that LLM calls are tracked with Langfuse."""
        from core.brain import Brain

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Mock Langfuse
        mock_generation = MagicMock()
        mock_observability.create_generation.return_value = mock_generation

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="anthropic/claude-3.5-sonnet",
                track_generation=True
            )

        # Verify generation was created
        mock_observability.create_generation.assert_called_once()
        call_kwargs = mock_observability.create_generation.call_args.kwargs
        assert call_kwargs['model'] == "anthropic/claude-3.5-sonnet"

        # Verify generation was updated with output
        mock_observability.update_generation.assert_called_once()
        update_kwargs = mock_observability.update_generation.call_args.kwargs
        assert update_kwargs['usage']['prompt_tokens'] == 10

        # Verify generation was ended
        mock_observability.end_generation.assert_called_once_with(mock_generation)

    @patch('core.brain.OpenAI')
    @patch('core.brain.observability')
    def test_generation_tracking_disabled(self, mock_observability, mock_openai):
        """Test that tracking can be disabled."""
        from core.brain import Brain

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="anthropic/claude-3.5-sonnet",
                track_generation=False
            )

        # Verify no generation tracking occurred
        mock_observability.create_generation.assert_not_called()

    @patch('core.brain.OpenAI')
    @patch('core.brain.observability')
    def test_generation_tracking_with_custom_metadata(self, mock_observability, mock_openai):
        """Test generation tracking with custom metadata."""
        from core.brain import Brain

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        mock_generation = MagicMock()
        mock_observability.create_generation.return_value = mock_generation

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="anthropic/claude-3.5-sonnet",
                track_generation=True,
                generation_name="scout_search",
                generation_metadata={"agent": "scout", "task": "search"}
            )

        # Verify custom metadata was passed
        call_kwargs = mock_observability.create_generation.call_args.kwargs
        assert call_kwargs['name'] == "scout_search"
        assert call_kwargs['metadata']['agent'] == "scout"
        assert call_kwargs['metadata']['task'] == "search"


class TestModelParameters:
    """Tests for model parameters and configuration."""

    @patch('core.brain.OpenAI')
    def test_temperature_parameter(self, mock_openai):
        """Test that temperature parameter is passed correctly."""
        from core.brain import Brain

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="anthropic/claude-3.5-sonnet",
                temperature=0.8
            )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs['temperature'] == 0.8

    @patch('core.brain.OpenAI')
    def test_max_tokens_parameter(self, mock_openai):
        """Test that max_tokens parameter is passed correctly."""
        from core.brain import Brain

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "anthropic/claude-3.5-sonnet"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            brain = Brain()
            response = brain.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="anthropic/claude-3.5-sonnet",
                max_tokens=500
            )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs['max_tokens'] == 500
