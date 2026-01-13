# Langfuse Cloud Setup Instructions

Follow these steps to get your Langfuse Cloud API keys and test the observability integration.

## Step 1: Create Langfuse Cloud Account

1. Go to https://cloud.langfuse.com
2. Sign up for a free account (or sign in if you already have one)
3. You'll be taken to your dashboard

## Step 2: Create a Project

1. In the Langfuse dashboard, click "New Project" (if you don't have one already)
2. Give it a name like "OpenAgent" or "Agent System"
3. Click "Create Project"

## Step 3: Get Your API Keys

1. In your project, go to **Settings** (gear icon in sidebar)
2. Click on **"API Keys"** tab
3. You'll see your keys:
   - **Public Key** (starts with `pk-lf-...`)
   - **Secret Key** (starts with `sk-lf-...`)
4. Copy both keys (you may need to click "Reveal" for the secret key)

## Step 4: Create .env File

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your keys:
   ```bash
   nano .env
   ```

3. Replace the placeholder values:
   ```
   LANGFUSE_PUBLIC_KEY=pk-lf-YOUR_ACTUAL_PUBLIC_KEY_HERE
   LANGFUSE_SECRET_KEY=sk-lf-YOUR_ACTUAL_SECRET_KEY_HERE
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

4. Save and exit (Ctrl+O, Enter, Ctrl+X in nano)

## Step 5: Run Integration Tests

Once your `.env` file is set up, run the integration tests:

```bash
# Activate virtual environment
source venv/bin/activate

# Run integration tests
python -m pytest tests/integration/test_langfuse_integration.py -v -s

# Or run the manual verification script directly
python tests/integration/test_langfuse_integration.py
```

## Step 6: Verify in Langfuse Dashboard

After running the tests:

1. Go back to https://cloud.langfuse.com
2. Click on your project
3. You should see:
   - **Traces** in the sidebar - click to view all traces
   - Look for traces with names like `integration_test_*` or `manual_verification_*`
   - Click on a trace to see details including:
     - Metadata (tags, user ID, timestamps)
     - Generation spans (simulated LLM calls)
     - Token usage (prompt_tokens, completion_tokens)

## Troubleshooting

### Error: "Failed to connect to Langfuse Cloud"
- Check that your API keys are correct
- Make sure there are no extra spaces in the .env file
- Verify the keys start with `pk-lf-` and `sk-lf-`

### Error: "LANGFUSE_PUBLIC_KEY environment variable is required"
- Make sure the .env file is in the project root directory
- Ensure the file is named `.env` (not `.env.txt`)
- Try running: `cat .env` to verify the contents

### Traces not appearing in dashboard
- Wait 5-10 seconds and refresh the page
- Make sure you're looking at the correct project
- Check the date filter in the dashboard (should include today)

## Security Note

**IMPORTANT**: Never commit your `.env` file to git!
- The `.env` file is already in `.gitignore`
- Your API keys should remain secret
- If you accidentally expose your keys, regenerate them in the Langfuse dashboard
