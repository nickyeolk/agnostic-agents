"""
Brain module - LLM caller for OpenRouter.
Handles LLM completions, tool call parsing, error handling, and observability.
"""
import os
import json
import time
from typing import Dict, Any, List, Optional, Union
from openai import OpenAI
import openai

from core import observability


class BrainError(Exception):
    """Custom exception for Brain errors."""
    pass


class Brain:
    """
    Brain - LLM caller using OpenRouter API.

    Handles:
    - LLM completions via OpenRouter
    - Tool call parsing
    - Error handling and retries
    - Langfuse observability integration
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Brain client.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            base_url: OpenRouter API base URL
            max_retries: Maximum number of retries on errors
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Set it in .env file or pass as argument."
            )

        self.base_url = base_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize OpenAI client for OpenRouter
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        track_generation: bool = True,
        generation_name: Optional[str] = None,
        generation_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a completion request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            tools: Optional list of tool definitions
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            track_generation: Whether to track with Langfuse
            generation_name: Custom name for Langfuse generation
            generation_metadata: Custom metadata for Langfuse generation

        Returns:
            Dict containing:
                - content: Response text (if no tool calls)
                - tool_calls: List of tool call dicts (if any)
                - model: Model that was used
                - usage: Token usage dict

        Raises:
            BrainError: If max retries exceeded or unrecoverable error
        """
        # Start Langfuse generation tracking if enabled
        generation = None
        if track_generation:
            generation = observability.create_generation(
                name=generation_name or f"llm_call_{model.split('/')[-1]}",
                model=model,
                input_data={
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                metadata=generation_metadata or {},
                model_parameters={
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )

        # Attempt completion with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Make API call
                call_kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }

                if max_tokens:
                    call_kwargs["max_tokens"] = max_tokens

                if tools:
                    call_kwargs["tools"] = tools

                response = self.client.chat.completions.create(**call_kwargs)

                # Parse response
                result = self._parse_response(response)

                # Update Langfuse generation with output
                if track_generation and generation:
                    observability.update_generation(
                        generation=generation,
                        output_data=result,
                        usage={
                            "prompt_tokens": result["usage"]["prompt_tokens"],
                            "completion_tokens": result["usage"]["completion_tokens"],
                            "total_tokens": result["usage"]["total_tokens"]
                        }
                    )
                    observability.end_generation(generation)

                return result

            except (openai.RateLimitError, openai.APIError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Wait before retrying
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    # Max retries exceeded
                    if track_generation and generation:
                        observability.end_generation(generation)
                    raise BrainError(
                        f"Max retries ({self.max_retries}) exceeded. Last error: {str(e)}"
                    )

            except Exception as e:
                # Unrecoverable error
                if track_generation and generation:
                    observability.end_generation(generation)
                raise BrainError(f"LLM call failed: {str(e)}")

        # Should not reach here, but just in case
        if track_generation and generation:
            observability.end_generation(generation)
        raise BrainError(f"Max retries exceeded. Last error: {str(last_error)}")

    def _parse_response(self, response) -> Dict[str, Any]:
        """
        Parse OpenAI-format response into standardized dict.

        Args:
            response: OpenAI completion response object

        Returns:
            Dict with content, tool_calls, model, and usage
        """
        message = response.choices[0].message

        result = {
            "content": message.content,
            "tool_calls": None,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

        # Parse tool calls if present
        if message.tool_calls:
            result["tool_calls"] = []
            for tool_call in message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments)
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": arguments
                    })
                except json.JSONDecodeError as e:
                    # Handle malformed JSON
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": {},
                        "error": f"Failed to parse arguments: {str(e)}"
                    })

        return result
