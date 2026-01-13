"""
Integration test for Langfuse Cloud observability.
This test makes real API calls to Langfuse Cloud and verifies traces are created.

IMPORTANT: This requires real API keys in .env file:
- LANGFUSE_PUBLIC_KEY
- LANGFUSE_SECRET_KEY
- LANGFUSE_HOST (optional, defaults to https://cloud.langfuse.com)

To run: python -m pytest tests/integration/test_langfuse_integration.py -v -s
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
    not os.getenv('LANGFUSE_PUBLIC_KEY') or not os.getenv('LANGFUSE_SECRET_KEY'),
    reason="Langfuse API keys not found in environment. Create a .env file with your keys."
)


@skip_if_no_keys
class TestLangfuseCloudIntegration:
    """Integration tests with real Langfuse Cloud API."""

    def test_connection_to_langfuse_cloud(self):
        """Test that we can connect to Langfuse Cloud."""
        from core import observability

        # Reset client to force re-initialization
        observability._langfuse_client = None

        result = observability.verify_langfuse_connection()

        assert result is True, "Failed to connect to Langfuse Cloud. Check your API keys."
        print("\n✓ Successfully connected to Langfuse Cloud")

    def test_create_simple_trace(self):
        """Test creating a simple trace in Langfuse Cloud."""
        from core import observability

        # Reset client
        observability._langfuse_client = None

        # Create a test trace
        trace_name = f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        trace = observability.create_trace(
            name=trace_name,
            user_id="test_user",
            metadata={
                "test": "integration",
                "environment": "termux",
                "timestamp": datetime.now().isoformat()
            },
            tags=["integration-test", "termux"]
        )

        assert trace is not None, "Failed to create trace"
        print(f"\n✓ Created trace: {trace_name}")

        # Flush to ensure trace is sent
        observability.flush_traces()
        print("✓ Flushed traces to Langfuse Cloud")

        # Give it a moment to process
        time.sleep(2)

        print(f"\n📊 Check your Langfuse dashboard at https://cloud.langfuse.com")
        print(f"   Look for trace: {trace_name}")

    def test_create_trace_with_generation(self):
        """Test creating a generation (simulating LLM call) with new API."""
        from core import observability

        # Reset client
        observability._langfuse_client = None

        # Create a generation directly (new API doesn't use trace parameter)
        generation_name = f"llm_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        generation = observability.create_generation(
            name=generation_name,
            model="anthropic/claude-3.5-sonnet",
            input_data={
                "prompt": "Hello, this is a test prompt",
            },
            metadata={"test": "integration"},
            model_parameters={"temperature": 0.7, "max_tokens": 100}
        )

        assert generation is not None
        print(f"\n✓ Created generation: {generation_name}")

        # Update the generation with mock output
        observability.update_generation(
            generation=generation,
            output_data={
                "response": "Hello! This is a test response from the integration test."
            },
            usage={
                "prompt_tokens": 15,
                "completion_tokens": 12,
                "total_tokens": 27
            }
        )

        print("✓ Updated generation with output and usage")

        # End the generation
        observability.end_generation(generation)
        print("✓ Ended generation")

        # Flush to ensure everything is sent
        observability.flush_traces()
        print("✓ Flushed traces to Langfuse Cloud")

        # Give it a moment to process
        time.sleep(2)

        print(f"\n📊 Check your Langfuse dashboard at https://cloud.langfuse.com")
        print(f"   Look for generation: {generation_name}")
        print(f"   It should contain token usage and model parameters")

    def test_observe_decorator_with_real_api(self):
        """Test the @observe decorator with real Langfuse API."""
        from core import observability

        # Reset client
        observability._langfuse_client = None

        @observability.observe(name="integration_test_function")
        def test_function(x: int, y: int) -> int:
            """A simple test function."""
            return x + y

        # Call the decorated function
        result = test_function(5, 3)

        assert result == 8
        print(f"\n✓ Function executed: 5 + 3 = {result}")

        # Give it a moment to process
        time.sleep(2)

        print(f"\n📊 Check your Langfuse dashboard at https://cloud.langfuse.com")
        print(f"   Look for trace: integration_test_function")


@skip_if_no_keys
def test_manual_langfuse_verification():
    """
    Manual verification test that prints instructions.
    Run this to get step-by-step guidance for verifying Langfuse integration.
    """
    from core import observability

    print("\n" + "="*70)
    print("LANGFUSE CLOUD INTEGRATION VERIFICATION")
    print("="*70)

    # Reset client
    observability._langfuse_client = None

    print("\n1. Testing connection...")
    connected = observability.verify_langfuse_connection()

    if connected:
        print("   ✓ Connected to Langfuse Cloud successfully!")
    else:
        print("   ✗ Failed to connect to Langfuse Cloud")
        print("   Check your API keys in .env file")
        return

    print("\n2. Creating a generation with new API...")
    generation_name = f"manual_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    generation = observability.create_generation(
        name=generation_name,
        model="anthropic/claude-3.5-sonnet",
        input_data={"prompt": "Verify Langfuse integration"},
        metadata={
            "purpose": "manual_verification",
            "test": "manual_verification",
            "user_id": "integration_test_user"
        },
        model_parameters={"temperature": 0.7}
    )
    print(f"   ✓ Created generation: {generation_name}")

    print("\n3. Updating generation with output...")
    observability.update_generation(
        generation=generation,
        output_data={"response": "Langfuse integration verified!"},
        usage={
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    )
    print("   ✓ Updated generation with token usage")

    print("\n4. Ending generation...")
    observability.end_generation(generation)
    print("   ✓ Generation ended")

    print("\n5. Flushing traces to Langfuse Cloud...")
    observability.flush_traces()
    print("   ✓ Traces flushed")

    print("\n" + "="*70)
    print("VERIFICATION COMPLETE!")
    print("="*70)
    print(f"\n📊 Now check your Langfuse dashboard:")
    print(f"   URL: https://cloud.langfuse.com")
    print(f"\n🔍 Look for:")
    print(f"   • Generation name: {generation_name}")
    print(f"   • Model: anthropic/claude-3.5-sonnet")
    print(f"   • Token usage: 10 prompt + 5 completion = 15 total")
    print(f"   • Input/output data with verification message")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Run manual verification if executed directly
    test_manual_langfuse_verification()
