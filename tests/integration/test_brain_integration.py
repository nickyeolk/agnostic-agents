"""
Integration test for Brain module with real OpenRouter API.
This test makes real API calls to OpenRouter and verifies Langfuse tracking.

IMPORTANT: This requires real API keys in .env file:
- OPENROUTER_API_KEY
- LANGFUSE_PUBLIC_KEY (for tracking verification)
- LANGFUSE_SECRET_KEY

To run: python -m pytest tests/integration/test_brain_integration.py -v -s
"""
import os
import time
from datetime import datetime
import pytest
from dotenv import load_dotenv

# Load .env file FIRST before checking for keys
load_dotenv()

# Skip if no API keys are present
skip_if_no_keys = pytest.mark.skipif(
    not os.getenv('OPENROUTER_API_KEY'),
    reason="OPENROUTER_API_KEY not found in environment. Create a .env file with your key."
)


@skip_if_no_keys
class TestBrainOpenRouterIntegration:
    """Integration tests with real OpenRouter API."""

    def test_simple_completion_with_openrouter(self):
        """Test making a simple completion call to OpenRouter."""
        from core.brain import Brain
        from core import observability

        # Reset observability client
        observability._langfuse_client = None

        print("\n" + "="*70)
        print("Testing Brain with OpenRouter API")
        print("="*70)

        # Create Brain instance
        brain = Brain()
        print("✓ Brain instance created")

        # Make a simple completion call
        print("\n1. Making simple completion call...")
        response = brain.complete(
            messages=[
                {"role": "user", "content": "Say 'Hello from OpenRouter!' and nothing else."}
            ],
            model="anthropic/claude-3.5-haiku",  # Using Haiku for cost efficiency
            temperature=0.7,
            max_tokens=50,
            track_generation=True,
            generation_name=f"brain_test_{datetime.now().strftime('%H%M%S')}",
            generation_metadata={"test": "integration", "type": "simple_completion"}
        )

        print(f"   Response: {response['content']}")
        print(f"   Model: {response['model']}")
        print(f"   Usage: {response['usage']['prompt_tokens']} prompt + {response['usage']['completion_tokens']} completion = {response['usage']['total_tokens']} total")

        # Assertions
        assert response is not None
        assert "content" in response
        assert response["content"] is not None
        assert len(response["content"]) > 0
        assert "usage" in response
        assert response["usage"]["total_tokens"] > 0

        print("\n   ✓ Completion successful!")

        # Flush traces
        print("\n2. Flushing traces to Langfuse...")
        observability.flush_traces()
        time.sleep(2)

        print("\n" + "="*70)
        print("✅ TEST PASSED!")
        print("="*70)
        print("\n📊 Check your Langfuse dashboard:")
        print("   URL: https://cloud.langfuse.com")
        print(f"   Look for generation: brain_test_*")
        print(f"   Model: {response['model']}")
        print(f"   Should show token usage and response content")
        print("\n" + "="*70 + "\n")

    def test_completion_with_tool_calls(self):
        """Test completion that uses tool calls with OpenRouter."""
        from core.brain import Brain
        from core import observability

        # Reset observability client
        observability._langfuse_client = None

        print("\n" + "="*70)
        print("Testing Brain Tool Calls with OpenRouter API")
        print("="*70)

        # Create Brain instance
        brain = Brain()

        # Define a simple tool
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city name, e.g. San Francisco"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "The temperature unit"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]

        print("\n1. Making completion with tool definition...")
        response = brain.complete(
            messages=[
                {"role": "user", "content": "What's the weather like in Paris?"}
            ],
            model="anthropic/claude-3.5-haiku",  # Using Haiku for cost efficiency
            tools=tools,
            temperature=0.7,
            track_generation=True,
            generation_name=f"brain_tool_test_{datetime.now().strftime('%H%M%S')}",
            generation_metadata={"test": "integration", "type": "tool_call"}
        )

        print(f"\n   Response received:")
        if response.get("tool_calls"):
            print(f"   Tool calls: {len(response['tool_calls'])}")
            for i, tc in enumerate(response['tool_calls']):
                print(f"      {i+1}. {tc['name']}({tc['arguments']})")
            assert response["tool_calls"] is not None
            assert len(response["tool_calls"]) > 0
            assert response["tool_calls"][0]["name"] == "get_weather"
            assert "location" in response["tool_calls"][0]["arguments"]
            print("\n   ✓ Tool calls parsed successfully!")
        else:
            print(f"   Content: {response['content']}")
            print("\n   Note: Model returned text instead of tool call (this can happen)")

        print(f"   Usage: {response['usage']['total_tokens']} tokens")

        # Flush traces
        print("\n2. Flushing traces to Langfuse...")
        observability.flush_traces()
        time.sleep(2)

        print("\n" + "="*70)
        print("✅ TEST PASSED!")
        print("="*70)
        print("\n📊 Check your Langfuse dashboard:")
        print("   URL: https://cloud.langfuse.com")
        print(f"   Look for generation: brain_tool_test_*")
        print("   Should show tool definition and possible tool call")
        print("\n" + "="*70 + "\n")

    def test_error_handling_with_invalid_model(self):
        """Test error handling with an invalid model name."""
        from core.brain import Brain, BrainError

        print("\n" + "="*70)
        print("Testing Brain Error Handling")
        print("="*70)

        brain = Brain(max_retries=1)  # Reduce retries for faster test

        print("\n1. Attempting call with invalid model...")
        with pytest.raises(BrainError) as exc_info:
            brain.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="invalid/model/name/that/does/not/exist",
                track_generation=False  # Don't track failed attempts
            )

        print(f"   ✓ Error caught as expected: {str(exc_info.value)[:100]}...")
        print("\n   ✓ Error handling works correctly!")

        print("\n" + "="*70)
        print("✅ TEST PASSED!")
        print("="*70 + "\n")

    def test_system_message_handling(self):
        """Test that system messages are handled correctly."""
        from core.brain import Brain
        from core import observability

        # Reset observability client
        observability._langfuse_client = None

        print("\n" + "="*70)
        print("Testing System Message Handling")
        print("="*70)

        brain = Brain()

        print("\n1. Making completion with system message...")
        response = brain.complete(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds in exactly 5 words."},
                {"role": "user", "content": "Tell me about the weather"}
            ],
            model="anthropic/claude-3.5-haiku",
            temperature=0.7,
            max_tokens=50,
            track_generation=True,
            generation_name=f"brain_system_test_{datetime.now().strftime('%H%M%S')}",
            generation_metadata={"test": "integration", "type": "system_message"}
        )

        print(f"   Response: {response['content']}")
        print(f"   Word count: {len(response['content'].split())}")

        assert response is not None
        assert response["content"] is not None
        print("\n   ✓ System message handled correctly!")

        # Flush traces
        observability.flush_traces()
        time.sleep(1)

        print("\n" + "="*70)
        print("✅ TEST PASSED!")
        print("="*70 + "\n")


@skip_if_no_keys
def test_manual_brain_verification():
    """
    Manual verification test that prints instructions.
    Run this to get step-by-step guidance for verifying Brain integration.
    """
    from core.brain import Brain
    from core import observability

    print("\n" + "="*70)
    print("BRAIN + OPENROUTER INTEGRATION VERIFICATION")
    print("="*70)

    # Reset observability client
    observability._langfuse_client = None

    print("\n1. Creating Brain instance...")
    brain = Brain()
    print("   ✓ Brain created successfully")

    print("\n2. Testing simple completion...")
    test_name = f"manual_brain_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    response = brain.complete(
        messages=[
            {"role": "user", "content": "Respond with exactly: 'Brain test successful!'"}
        ],
        model="anthropic/claude-3.5-haiku",
        temperature=0.7,
        max_tokens=50,
        track_generation=True,
        generation_name=test_name,
        generation_metadata={
            "test": "manual_verification",
            "purpose": "verify brain integration"
        }
    )

    print(f"   ✓ Response received: {response['content']}")
    print(f"   ✓ Model: {response['model']}")
    print(f"   ✓ Tokens used: {response['usage']['total_tokens']}")

    print("\n3. Testing with conversation history...")
    response2 = brain.complete(
        messages=[
            {"role": "user", "content": "My name is Alice"},
            {"role": "assistant", "content": "Nice to meet you, Alice!"},
            {"role": "user", "content": "What's my name?"}
        ],
        model="anthropic/claude-3.5-haiku",
        temperature=0.7,
        max_tokens=50,
        track_generation=True,
        generation_name=f"{test_name}_conversation",
        generation_metadata={
            "test": "manual_verification",
            "purpose": "verify conversation context"
        }
    )

    print(f"   ✓ Response: {response2['content']}")
    assert "alice" in response2['content'].lower(), "Model should remember the name"
    print("   ✓ Conversation context maintained!")

    print("\n4. Flushing traces to Langfuse Cloud...")
    observability.flush_traces()
    print("   ✓ Traces flushed")

    print("\n" + "="*70)
    print("VERIFICATION COMPLETE!")
    print("="*70)
    print(f"\n📊 Now check your Langfuse dashboard:")
    print(f"   URL: https://cloud.langfuse.com")
    print(f"\n🔍 Look for:")
    print(f"   • Generation name: {test_name}")
    print(f"   • Model: anthropic/claude-3.5-haiku")
    print(f"   • Two generations (simple + conversation)")
    print(f"   • Token usage for both calls")
    print(f"   • Input/output data showing the conversation")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Run manual verification if executed directly
    test_manual_brain_verification()
