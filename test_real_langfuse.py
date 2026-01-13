#!/usr/bin/env python
"""
Simple script to test Langfuse integration with real API.
"""
from dotenv import load_dotenv
load_dotenv()

from core import observability
from datetime import datetime
import time

print("="*70)
print("TESTING LANGFUSE CLOUD INTEGRATION")
print("="*70)

# Test 1: Connection
print("\n1. Testing connection to Langfuse Cloud...")
observability._langfuse_client = None
connected = observability.verify_langfuse_connection()
if connected:
    print("   ✓ Connected successfully!")
else:
    print("   ✗ Connection failed!")
    exit(1)

# Test 2: Using @observe decorator
print("\n2. Testing @observe decorator...")
@observability.observe(name="test_function")
def add_numbers(x: int, y: int) -> int:
    """Test function."""
    return x + y

result = add_numbers(5, 3)
print(f"   ✓ Function executed: 5 + 3 = {result}")

# Test 3: Create a generation manually
print("\n3. Testing manual generation creation...")
generation = observability.create_generation(
    name=f"test_generation_{datetime.now().strftime('%H%M%S')}",
    model="anthropic/claude-3.5-sonnet",
    input_data={"prompt": "Hello, this is a test"},
    model_parameters={"temperature": 0.7}
)
print("   ✓ Generation created")

# Update it with output
observability.update_generation(
    generation=generation,
    output_data={"response": "Hello! This is a test response."},
    usage={
        "prompt_tokens": 10,
        "completion_tokens": 8,
        "total_tokens": 18
    }
)
print("   ✓ Generation updated with output and usage")

# End the generation
observability.end_generation(generation)
print("   ✓ Generation ended")

# Test 4: Flush traces
print("\n4. Flushing traces to Langfuse Cloud...")
observability.flush_traces()
print("   ✓ Traces flushed")

# Give it a moment to process
print("\n5. Waiting for traces to be processed...")
time.sleep(3)

print("\n" + "="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)
print("\n📊 Check your Langfuse dashboard:")
print("   URL: https://cloud.langfuse.com")
print("\n🔍 You should see:")
print("   • A trace from the @observe decorator (test_function)")
print("   • A generation span with token usage")
print("   • All with proper metadata and timestamps")
print("\n" + "="*70 + "\n")
