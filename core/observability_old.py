"""
Observability module for Langfuse Cloud integration.
Provides trace creation, generation spans, and decorators for LLM observability.
"""
import os
from typing import Optional, Dict, Any, Callable
from functools import wraps
import logging

from langfuse import Langfuse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Module-level logger
logger = logging.getLogger(__name__)

# Global Langfuse client instance
_langfuse_client: Optional[Langfuse] = None
_current_trace = None


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


def create_trace(
    name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
):
    """
    Create a new trace in Langfuse.

    Args:
        name: Name of the trace (e.g., "agent_run", "marketing_plan_generation")
        user_id: Optional user identifier
        session_id: Optional session identifier
        metadata: Optional metadata dictionary
        tags: Optional list of tags

    Returns:
        Langfuse trace object
    """
    global _current_trace

    client = get_langfuse_client()

    trace = client.trace(
        name=name,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata or {},
        tags=tags or []
    )

    _current_trace = trace
    logger.debug(f"Created trace: {name}")

    return trace


def get_current_trace():
    """
    Get the current active trace.

    Returns:
        Current trace object or None
    """
    return _current_trace


def create_generation_span(
    trace,
    name: str,
    model: str,
    input_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Create a generation span for LLM calls within a trace.

    Args:
        trace: Parent trace object
        name: Name of the generation (e.g., "scout_query", "architect_draft")
        model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
        input_data: Input data (prompt, messages, etc.)
        metadata: Optional metadata (temperature, max_tokens, etc.)

    Returns:
        Generation span object
    """
    generation = trace.generation(
        name=name,
        model=model,
        input=input_data,
        metadata=metadata or {}
    )

    logger.debug(f"Created generation span: {name} with model: {model}")

    return generation


def update_generation(
    generation,
    output_data: Dict[str, Any],
    usage: Optional[Dict[str, int]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Update a generation span with output and usage information.

    Args:
        generation: Generation span object
        output_data: LLM output data
        usage: Token usage information (prompt_tokens, completion_tokens, total_tokens)
        metadata: Additional metadata to add
    """
    update_kwargs = {
        'output': output_data
    }

    if usage:
        update_kwargs['usage'] = usage

    if metadata:
        update_kwargs['metadata'] = metadata

    generation.update(**update_kwargs)
    logger.debug(f"Updated generation with output")


def observe(name: Optional[str] = None, capture_input: bool = True, capture_output: bool = True):
    """
    Decorator to automatically create traces for functions.

    Args:
        name: Optional name for the trace (defaults to function name)
        capture_input: Whether to capture function inputs
        capture_output: Whether to capture function outputs

    Usage:
        @observe(name="process_data")
        def process_data(data: dict) -> dict:
            return {"result": data}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace_name = name or func.__name__

            # Capture inputs if requested
            input_data = {}
            if capture_input:
                input_data = {
                    'args': str(args) if args else None,
                    'kwargs': kwargs if kwargs else None
                }

            # Create trace
            trace = create_trace(
                name=trace_name,
                metadata={'function': func.__name__, 'input': input_data}
            )

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Capture output if requested
                if capture_output and trace:
                    trace.update(output={'result': str(result)})

                return result
            except Exception as e:
                # Log error in trace
                if trace:
                    trace.update(
                        output={'error': str(e)},
                        metadata={'status': 'error'}
                    )
                raise
            finally:
                # Flush to ensure trace is sent
                client = get_langfuse_client()
                client.flush()

        return wrapper
    return decorator


def observe_llm_call(model: str, capture_io: bool = True):
    """
    Decorator to automatically create generation spans for LLM calls.

    Args:
        model: Model identifier
        capture_io: Whether to capture input/output

    Usage:
        @observe_llm_call(model="anthropic/claude-3.5-sonnet")
        def call_llm(prompt: str) -> str:
            return llm.complete(prompt)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace = get_current_trace()

            if not trace:
                # Create a trace if none exists
                trace = create_trace(name=f"llm_call_{func.__name__}")

            # Capture input
            input_data = {}
            if capture_io:
                input_data = {
                    'function': func.__name__,
                    'args': str(args) if args else None,
                    'kwargs': kwargs if kwargs else None
                }

            # Create generation span
            generation = create_generation_span(
                trace=trace,
                name=func.__name__,
                model=model,
                input_data=input_data
            )

            try:
                # Execute LLM call
                result = func(*args, **kwargs)

                # Update with output
                if capture_io and generation:
                    update_generation(
                        generation=generation,
                        output_data={'result': str(result)}
                    )

                return result
            except Exception as e:
                # Log error in generation
                if generation:
                    update_generation(
                        generation=generation,
                        output_data={'error': str(e)},
                        metadata={'status': 'error'}
                    )
                raise
            finally:
                # Flush to ensure span is sent
                client = get_langfuse_client()
                client.flush()

        return wrapper
    return decorator


def verify_langfuse_connection() -> bool:
    """
    Verify connection to Langfuse Cloud.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        client = get_langfuse_client()

        # Try to auth check or create a test trace
        # Note: Langfuse SDK might not have auth_check, so we'll just try to use it
        test_trace = client.trace(name="connection_test")
        client.flush()

        logger.info("Langfuse connection verified successfully")
        return True
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
