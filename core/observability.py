"""
Observability module for Langfuse Cloud integration (Updated for correct SDK API).
Provides generation tracking and decorators for LLM observability.
"""
import os
from typing import Optional, Dict, Any
import logging

from langfuse import Langfuse, observe as langfuse_observe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Module-level logger
logger = logging.getLogger(__name__)

# Global Langfuse client instance
_langfuse_client: Optional[Langfuse] = None


def init_langfuse_client() -> Langfuse:
    """
    Initialize Langfuse client with environment variables.

    Returns:
        Langfuse: Initialized Langfuse client

    Raises:
        ValueError: If required environment variables are missing
    """
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')

    if not public_key:
        raise ValueError("LANGFUSE_PUBLIC_KEY environment variable is required")
    if not secret_key:
        raise ValueError("LANGFUSE_SECRET_KEY environment variable is required")

    logger.info(f"Initializing Langfuse client with host: {host}")

    client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host
    )

    return client


def get_langfuse_client() -> Langfuse:
    """
    Get or create the global Langfuse client instance.

    Returns:
        Langfuse: The global Langfuse client
    """
    global _langfuse_client

    if _langfuse_client is None:
        _langfuse_client = init_langfuse_client()

    return _langfuse_client


def create_generation(
    name: str,
    model: str,
    input_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    model_parameters: Optional[Dict[str, Any]] = None
):
    """
    Create a generation span for LLM calls.

    Args:
        name: Name of the generation (e.g., "scout_query", "architect_draft")
        model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
        input_data: Input data (prompt, messages, etc.)
        metadata: Optional metadata
        model_parameters: Model parameters (temperature, max_tokens, etc.)

    Returns:
        LangfuseGeneration object
    """
    client = get_langfuse_client()

    generation = client.start_generation(
        name=name,
        model=model,
        input=input_data,
        metadata=metadata or {},
        model_parameters=model_parameters or {}
    )

    logger.debug(f"Created generation: {name} with model: {model}")

    return generation


def update_generation(
    generation,
    output_data: Any,
    usage: Optional[Dict[str, int]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Update a generation span with output and usage information.

    Args:
        generation: LangfuseGeneration object
        output_data: LLM output data
        usage: Token usage dict with prompt_tokens, completion_tokens, total_tokens
        metadata: Additional metadata to add
    """
    update_kwargs = {
        'output': output_data
    }

    if usage:
        update_kwargs['usage_details'] = usage

    if metadata:
        update_kwargs['metadata'] = metadata

    generation.update(**update_kwargs)
    logger.debug(f"Updated generation with output")


def end_generation(generation):
    """
    End a generation span.

    Args:
        generation: LangfuseGeneration object
    """
    generation.end()
    logger.debug("Ended generation")


# Export the langfuse observe decorator for easy use
observe = langfuse_observe


def verify_langfuse_connection() -> bool:
    """
    Verify connection to Langfuse Cloud.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        client = get_langfuse_client()
        result = client.auth_check()

        if result:
            logger.info("Langfuse connection verified successfully")
            return True
        else:
            logger.error("Langfuse auth check returned False")
            return False
    except Exception as e:
        logger.error(f"Langfuse connection verification failed: {e}")
        return False


def flush_traces():
    """
    Flush all pending traces to Langfuse Cloud.
    Call this before application exit to ensure all traces are sent.
    """
    client = get_langfuse_client()
    client.flush()
    logger.info("Flushed all pending traces to Langfuse")


# For backwards compatibility, keep simple wrappers
def create_trace(*args, **kwargs):
    """Legacy method - use @observe decorator instead."""
    logger.warning("create_trace is deprecated. Use @observe decorator instead.")
    # Return a mock object that won't break existing code
    class MockTrace:
        def generation(self, *args, **kwargs):
            return create_generation(*args, **kwargs)
        def update(self, *args, **kwargs):
            pass
    return MockTrace()


def get_current_trace():
    """Legacy method - traces are managed automatically by @observe decorator."""
    logger.warning("get_current_trace is deprecated. Use @observe decorator instead.")
    return None


def create_generation_span(*args, **kwargs):
    """Legacy wrapper for create_generation."""
    return create_generation(*args, **kwargs)


def observe_llm_call(model: str, capture_io: bool = True):
    """
    Decorator to observe LLM calls using Langfuse.

    Args:
        model: Model identifier
        capture_io: Whether to capture input/output

    Usage:
        @observe_llm_call(model="anthropic/claude-3.5-sonnet")
        def call_llm(prompt: str) -> str:
            return llm.complete(prompt)
    """
    # Use the langfuse observe decorator with as_type='generation'
    return langfuse_observe(as_type='generation', capture_input=capture_io, capture_output=capture_io)
