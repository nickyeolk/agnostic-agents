"""
Tests for observability module with Langfuse Cloud integration.
Tests Langfuse client initialization, generation tracking, and decorators.
"""
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import pytest


class TestLangfuseClientInitialization:
    """Tests for Langfuse client initialization."""

    def test_init_langfuse_client_with_env_vars(self):
        """Test that Langfuse client initializes with environment variables."""
        from core import observability

        with patch.dict(os.environ, {
            'LANGFUSE_PUBLIC_KEY': 'pk-lf-test-key',
            'LANGFUSE_SECRET_KEY': 'sk-lf-test-secret',
            'LANGFUSE_HOST': 'https://cloud.langfuse.com'
        }):
            # Patch where it's used in the module
            with patch('core.observability.Langfuse') as mock_langfuse:
                # Reset module global state
                observability._langfuse_client = None

                client = observability.init_langfuse_client()

                # Verify Langfuse was called with correct parameters
                mock_langfuse.assert_called_once_with(
                    public_key='pk-lf-test-key',
                    secret_key='sk-lf-test-secret',
                    host='https://cloud.langfuse.com'
                )
                assert client is not None

    def test_init_langfuse_client_missing_keys_raises_error(self):
        """Test that missing API keys raise an error."""
        with patch.dict(os.environ, {}, clear=True):
            from core import observability
            observability._langfuse_client = None

            with pytest.raises(ValueError, match="LANGFUSE_PUBLIC_KEY"):
                observability.init_langfuse_client()

    def test_init_langfuse_client_uses_default_host(self):
        """Test that default host is used when not specified."""
        from core import observability

        with patch.dict(os.environ, {
            'LANGFUSE_PUBLIC_KEY': 'pk-lf-test-key',
            'LANGFUSE_SECRET_KEY': 'sk-lf-test-secret'
        }):
            # Patch where Langfuse is used, not where it's defined
            with patch('core.observability.Langfuse') as mock_langfuse:
                observability._langfuse_client = None

                client = observability.init_langfuse_client()

                # Should use default Langfuse Cloud host
                mock_langfuse.assert_called_once()
                call_args = mock_langfuse.call_args
                assert 'cloud.langfuse.com' in call_args.kwargs.get('host', '')


class TestGenerationTracking:
    """Tests for generation creation and management."""

    def test_create_generation(self):
        """Test creating a generation for LLM tracking."""
        from core import observability

        mock_client = MagicMock()
        mock_generation = MagicMock()
        mock_client.start_generation.return_value = mock_generation

        observability._langfuse_client = mock_client

        generation = observability.create_generation(
            name="test_llm_call",
            model="anthropic/claude-3.5-sonnet",
            input_data={"prompt": "Hello"},
            metadata={"test": True},
            model_parameters={"temperature": 0.7}
        )

        mock_client.start_generation.assert_called_once()
        call_kwargs = mock_client.start_generation.call_args.kwargs
        assert call_kwargs['name'] == "test_llm_call"
        assert call_kwargs['model'] == "anthropic/claude-3.5-sonnet"
        assert call_kwargs['input'] == {"prompt": "Hello"}
        assert call_kwargs['metadata'] == {"test": True}
        assert call_kwargs['model_parameters'] == {"temperature": 0.7}
        assert generation is not None

    def test_update_generation_with_output(self):
        """Test updating generation with output and usage."""
        from core import observability

        mock_generation = MagicMock()

        observability.update_generation(
            generation=mock_generation,
            output_data={"response": "Hello there!"},
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            },
            metadata={"status": "success"}
        )

        mock_generation.update.assert_called_once()
        call_kwargs = mock_generation.update.call_args.kwargs
        assert call_kwargs['output'] == {"response": "Hello there!"}
        assert call_kwargs['usage_details']['prompt_tokens'] == 10
        assert call_kwargs['usage_details']['completion_tokens'] == 5
        assert call_kwargs['metadata'] == {"status": "success"}

    def test_end_generation(self):
        """Test ending a generation."""
        from core import observability

        mock_generation = MagicMock()

        observability.end_generation(mock_generation)

        mock_generation.end.assert_called_once()


class TestObservabilityDecorators:
    """Tests for observability decorators."""

    def test_observe_decorator_is_available(self):
        """Test that @observe decorator is available."""
        from core import observability

        # Should be the langfuse observe decorator
        assert observability.observe is not None
        assert callable(observability.observe)

    def test_observe_llm_call_decorator(self):
        """Test that @observe_llm_call decorator is available."""
        from core import observability

        decorator = observability.observe_llm_call(model="test-model")
        assert decorator is not None
        assert callable(decorator)


class TestLangfuseConnection:
    """Tests for Langfuse Cloud connection verification."""

    def test_verify_connection_success(self):
        """Test successful connection verification."""
        from core import observability

        mock_client = MagicMock()
        mock_client.auth_check.return_value = True

        observability._langfuse_client = mock_client

        result = observability.verify_langfuse_connection()

        assert result is True
        mock_client.auth_check.assert_called_once()

    def test_verify_connection_failure(self):
        """Test connection verification with invalid credentials."""
        from core import observability

        mock_client = MagicMock()
        mock_client.auth_check.side_effect = Exception("Authentication failed")

        observability._langfuse_client = mock_client

        result = observability.verify_langfuse_connection()

        assert result is False


class TestBackwardsCompatibility:
    """Tests for backwards compatibility wrappers."""

    def test_create_trace_legacy_method(self):
        """Test that legacy create_trace method still works."""
        from core import observability

        mock_client = MagicMock()
        observability._langfuse_client = mock_client

        # Should return a mock trace object
        trace = observability.create_trace(name="test")
        assert trace is not None
        # Should have a generation method
        assert hasattr(trace, 'generation')

    def test_create_generation_span_legacy_wrapper(self):
        """Test that legacy create_generation_span wrapper works."""
        from core import observability

        mock_client = MagicMock()
        mock_generation = MagicMock()
        mock_client.start_generation.return_value = mock_generation

        observability._langfuse_client = mock_client

        generation = observability.create_generation_span(
            name="test",
            model="test-model"
        )

        assert generation is not None
        mock_client.start_generation.assert_called_once()


class TestFlushTraces:
    """Tests for trace flushing."""

    def test_flush_traces(self):
        """Test that flush_traces calls client.flush()."""
        from core import observability

        mock_client = MagicMock()
        observability._langfuse_client = mock_client

        observability.flush_traces()

        mock_client.flush.assert_called_once()
