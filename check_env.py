#!/usr/bin/env python
"""
Quick script to check if .env file is configured correctly for Langfuse Cloud.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

def check_env_setup():
    """Check if .env file exists and has required keys."""

    print("="*70)
    print("CHECKING LANGFUSE CLOUD CONFIGURATION")
    print("="*70)

    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("\n❌ .env file not found!")
        print("\nTo create it:")
        print("  1. Copy .env.example: cp .env.example .env")
        print("  2. Edit it: nano .env")
        print("  3. Add your Langfuse API keys from https://cloud.langfuse.com")
        print("\nSee LANGFUSE_SETUP.md for detailed instructions.")
        return False

    print("\n✓ .env file found")

    # Load environment variables
    load_dotenv()

    # Check required variables
    required_vars = {
        'LANGFUSE_PUBLIC_KEY': 'pk-lf-',
        'LANGFUSE_SECRET_KEY': 'sk-lf-',
    }

    all_good = True

    for var_name, prefix in required_vars.items():
        value = os.getenv(var_name)

        if not value:
            print(f"\n❌ {var_name} not found in .env file")
            all_good = False
        elif value == f"{prefix}your_key_here" or "example" in value.lower():
            print(f"\n❌ {var_name} contains placeholder value")
            print(f"   Please replace with your actual key from https://cloud.langfuse.com")
            all_good = False
        elif not value.startswith(prefix):
            print(f"\n❌ {var_name} has incorrect format")
            print(f"   Should start with: {prefix}")
            all_good = False
        else:
            # Mask the key for security
            masked = value[:10] + "..." + value[-4:]
            print(f"\n✓ {var_name}: {masked}")

    # Check optional host
    host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
    print(f"\n✓ LANGFUSE_HOST: {host}")

    print("\n" + "="*70)

    if all_good:
        print("✅ CONFIGURATION LOOKS GOOD!")
        print("="*70)
        print("\nYou can now run the integration tests:")
        print("  source venv/bin/activate")
        print("  python -m pytest tests/integration/test_langfuse_integration.py -v -s")
        print("\nOr run the manual verification:")
        print("  python tests/integration/test_langfuse_integration.py")
        return True
    else:
        print("❌ CONFIGURATION INCOMPLETE")
        print("="*70)
        print("\nPlease fix the issues above and run this script again.")
        print("\nFor help, see: LANGFUSE_SETUP.md")
        return False

if __name__ == "__main__":
    check_env_setup()
