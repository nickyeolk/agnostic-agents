# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a framework-agnostic AI agent system designed for building production-grade autonomous agents. The architecture enables switching between orchestration frameworks (LangGraph, CrewAI, Microsoft Agent Framework) without rewriting core business logic.

**Key Design Principles:**
- **Modular Logic Separation**: Brain (LLM logic) → Hands (Tools) → Glue (Adapters)
- **Framework Independence**: Core business logic is isolated from orchestrator-specific code
- **Local-First Observability**: OpenTelemetry with Langfuse for trace visualization
- **Unified Model Gateway**: OpenRouter for flexible model access
- **Keep it simple**: Avoid overly abstracted packages, keeping the code easy to read and learn. For example, use openai instead of langchain-openai.

## Architecture Layers

### 1. Core Layer (`/core`) - THE STABLE BUSINESS LOGIC
Contains framework-independent components that remain constant regardless of orchestrator choice:

- **`brain.py`**: Pure OpenAI SDK caller for LLM interactions via OpenRouter
- **`schema.py`**: Shared state models and data structures (use Pydantic with `default_factory`)
- **`tools.py`**: Pure Python tool functions with clear type hints and docstrings

### 2. Adapter Layer (`/adapters`) - THE SWAPPABLE ORCHESTRATION
Framework-specific implementations that wrap core logic:

- **`langgraph_app.py`**: Graph-based state machine for LangGraph
- **`crew_app.py`**: Role-based agentic logic for CrewAI
- **`ms_agent_app.py`**: Event-driven logic for Microsoft Agent Framework

### 3. Entry Point (`main.py`)
The orchestrator switcher that selects which adapter to use.

## Agent System Architecture

The reference implementation is an Autonomous Marketing Plan Generator with three agents:

**Market Scout (Researcher)**
- Performs real-time web research
- Triggered by Planner when knowledge gaps exist
- Returns structured data to inform strategy

**Architect (Planner)**
- Synthesizes research into marketing strategies
- Has autonomy to callback Scout for additional data
- Loops until quality benchmarks are met

**Judge (Critic)**
- Evaluates drafts against business goals
- Returns "REVISION_REQUIRED" or "APPROVED" status
- Triggers refinement loops back to Architect

### Agent Interaction Loops

**Information Loop** (Scout ↔ Architect):
- Occurs during drafting phase
- Architect emits tool calls when needing data
- Scout fetches and returns, Architect resumes from pause point

**Refinement Loop** (Architect ↔ Judge):
- Triggered after draft completion
- Cycles back to Architect on "REVISION_REQUIRED"
- Exits on "APPROVED" or max iteration limit (e.g., 5 turns)

## Observability Strategy

**OpenTelemetry (OTel) GenAI Semantic Conventions (2026)**:
- Instrument base OpenAI client for standardized traces
- Captures prompts, completion tokens, tool metadata
- Works consistently across all orchestrators

**Langfuse Cloud Integration**:
- Cloud-based trace inspection (https://cloud.langfuse.com)
- Cost monitoring and debugging visualization
- Receives traces via OTel OTLP export
- No local infrastructure required

## Infrastructure Requirements

**Database**: SQLite for conversation memory and thread management (single-file, no server needed)

**Observability Stack**: Langfuse Cloud (no local infrastructure required)

**Model Access**: OpenRouter API for unified model gateway

**Runtime**: Python 3.10+

**Environment**: Termux-compatible (no Docker required)

## Environment Configuration

Required environment variables in `.env`:
- `OPENROUTER_API_KEY`: Model access via OpenRouter
- `LANGFUSE_PUBLIC_KEY`: Langfuse Cloud public key (get from https://cloud.langfuse.com)
- `LANGFUSE_SECRET_KEY`: Langfuse Cloud secret key
- `LANGFUSE_HOST`: Langfuse Cloud endpoint (default: `https://cloud.langfuse.com`)
- `DATABASE_PATH`: SQLite database file path (default: `./data/agents.db`)

## Development Setup

```bash
# Install dependencies (Termux-compatible)
pip install -r requirements.txt

# Initialize database and directories
python setup.py init

# Run with specific orchestrator
python main.py --adapter langgraph
python main.py --adapter crew
python main.py --adapter ms-agent

# View trace files (if using file-based observability)
cat traces/trace_*.json | jq '.'
```

## Code Organization Guidelines

**When implementing core logic**:
- Keep `brain.py`, `schema.py`, and `tools.py` completely orchestrator-agnostic
- Use standard OpenAI SDK interfaces only
- Type hints and docstrings are mandatory for all tools
- No framework-specific imports in `/core`

**When implementing adapters**:
- Adapter code should be minimal "glue" wrapping core functions
- All orchestrator-specific logic stays in `/adapters`
- Adapters translate between framework conventions and core interfaces

**When adding new tools**:
- Define pure Python functions in `core/tools.py`
- Use clear type hints for input/output
- Document expected behavior in docstrings
- Ensure tools are stateless and testable

## Testing Strategy

**Unit Tests**: Test core logic independently of any orchestrator

**Integration Tests**: Test each adapter's ability to correctly wire core components

**Observability Tests**: Verify OTel traces are emitted correctly for all operations

## Model Selection

Use OpenRouter for flexible model access:
- Claude 3.5 Sonnet for complex reasoning tasks
- GPT-4o for balanced performance
- Experiment with other models via OpenRouter's unified interface

## Key Technical Constraints

- Python 3.10+ required
- All core business logic must remain framework-agnostic
- OTel instrumentation must capture all LLM calls
- Agent loops must have configurable iteration limits
- State models must use Pydantic validation
- Termux-compatible (no Docker, use SQLite)

---

## Implementation Plan (TDD Approach)

**Current Step**: Phase 2, Step 2.3 ⏳

### Phase 1: Project Foundation & Observability Infrastructure ✅ COMPLETE

**Step 1.1: Project Setup & Dependencies** ✅ COMPLETE
- [x] Create project structure (core/, adapters/, tests/, data/)
- [x] Write tests for: Directory structure validation (5 tests)
- [x] Implement: requirements.txt with core dependencies (openai, langfuse, pydantic, pytest)
- [x] Implement: .env.example template
- [x] Implement: .gitignore (exclude .env, data/, *.db)
- [x] Verify: `pip install -r requirements.txt` succeeds in Termux (Rust required via `pkg install rust`)

**Step 1.2: Langfuse Cloud Configuration** ✅ COMPLETE
- [x] Write tests for: Langfuse client initialization (3 tests)
- [x] Write tests for: Generation tracking and updates (3 tests)
- [x] Write tests for: Connection verification (2 tests)
- [x] Write tests for: Observability decorators (2 tests)
- [x] Write tests for: Backwards compatibility & flush (3 tests)
- [x] Implement: `core/observability.py` with correct Langfuse SDK API
- [x] Implement: Environment variable loading via python-dotenv
- [x] All 13 observability tests passing
- [x] Manual verification: Real traces verified in Langfuse Cloud UI ✅
- [x] Integration test: `test_real_langfuse.py` with live API

**Step 1.3: OpenAI Client Instrumentation** - SKIPPED (will integrate in Phase 2)
- Note: Observability is ready to wrap OpenAI calls in Phase 2 Brain implementation
- [ ] Write tests for: Tool calls are captured in traces
- [ ] Write tests for: Langfuse decorators on LLM functions
- [ ] Implement: Instrumented OpenAI client in `core/brain.py`
- [ ] Verify: Mock LLM calls produce traces in Langfuse

### Phase 2: Core Components with Observability

**Step 2.1: Core Schema** ✅ COMPLETE
- [x] Write tests for: Message models (5 tests)
- [x] Write tests for: Agent role enums and status (4 tests)
- [x] Write tests for: Conversation thread models (3 tests)
- [x] Write tests for: State models (3 tests)
- [x] Write tests for: Model validation edge cases (4 tests)
- [x] Implement: `core/schema.py` with all data models
- [x] All 19 schema tests passing
- [x] Pydantic v1 compatible (using dict() method)

**Step 2.2: Brain (LLM Caller)** ✅ COMPLETE
- [x] Write tests for: Basic LLM call via OpenRouter (4 tests)
- [x] Write tests for: Tool call parsing from LLM response (2 tests)
- [x] Write tests for: Error handling and retries (4 tests)
- [x] Write tests for: Langfuse traces for each LLM call (3 tests)
- [x] Write tests for: Model parameters (2 tests)
- [x] Implement: `core/brain.py` complete implementation
- [x] All 15 Brain tests passing
- [x] Total: 57 tests passing (100% pass rate)

**Step 2.3: Core Tools**
- [ ] Write tests for: Web search tool (mock HTTP)
- [ ] Write tests for: Data synthesis tool
- [ ] Write tests for: Tool function registration and calling
- [ ] Write tests for: Tool execution tracing
- [ ] Implement: `core/tools.py` with initial tools
- [ ] Verify: Tools execute and emit Langfuse observations

### Phase 3: Database Layer (SQLite)

**Step 3.1: SQLite Models**
- [ ] Write tests for: Conversation thread CRUD
- [ ] Write tests for: Message persistence
- [ ] Write tests for: Agent state storage
- [ ] Implement: SQLite schema creation script
- [ ] Implement: SQLAlchemy models (or simple SQL)
- [ ] Verify: Database file creation and queries work

**Step 3.2: Conversation Memory**
- [ ] Write tests for: Thread creation and retrieval
- [ ] Write tests for: Message append operations
- [ ] Write tests for: Context window management (token limits)
- [ ] Implement: Memory manager in `core/memory.py`
- [ ] Verify: Long conversations are handled correctly

### Phase 4: First Adapter (LangGraph)

**Step 4.1: LangGraph Adapter Setup**
- [ ] Write tests for: State graph construction
- [ ] Write tests for: Node execution with core functions
- [ ] Write tests for: Edge routing logic
- [ ] Implement: `adapters/langgraph_app.py`
- [ ] Verify: Simple graph executes end-to-end

**Step 4.2: Simple Agent Workflow**
- [ ] Write tests for: Single-agent task completion
- [ ] Write tests for: Tool calling within graph
- [ ] Write tests for: State persistence across nodes
- [ ] Implement: Basic agent in LangGraph adapter
- [ ] Verify: Agent completes simple task with full tracing

### Phase 5: Multi-Agent System

**Step 5.1: Market Scout Agent**
- [ ] Write tests for: Web research query generation
- [ ] Write tests for: Search result parsing
- [ ] Write tests for: Data extraction and structuring
- [ ] Implement: Scout agent logic in `core/agents/scout.py`
- [ ] Verify: Scout retrieves and structures web data

**Step 5.2: Architect Agent**
- [ ] Write tests for: Marketing plan generation
- [ ] Write tests for: Knowledge gap detection
- [ ] Write tests for: Scout callback mechanism
- [ ] Write tests for: Draft structuring
- [ ] Implement: Architect agent in `core/agents/architect.py`
- [ ] Verify: Architect generates draft with Scout integration

**Step 5.3: Judge Agent**
- [ ] Write tests for: Draft evaluation logic
- [ ] Write tests for: Revision requirement detection
- [ ] Write tests for: Approval criteria
- [ ] Write tests for: Feedback generation
- [ ] Implement: Judge agent in `core/agents/judge.py`
- [ ] Verify: Judge correctly evaluates drafts

**Step 5.4: Agent Loop Integration**
- [ ] Write tests for: Information loop (Scout ↔ Architect)
- [ ] Write tests for: Refinement loop (Architect ↔ Judge)
- [ ] Write tests for: Max iteration limits
- [ ] Write tests for: Loop termination conditions
- [ ] Implement: Loop orchestration in LangGraph adapter
- [ ] Verify: Full marketing plan generation works

### Phase 6: Additional Adapters (Optional)

**Step 6.1: CrewAI Adapter**
- [ ] Write tests for: CrewAI task definitions
- [ ] Write tests for: Role-based agent mapping
- [ ] Write tests for: Task dependencies
- [ ] Implement: `adapters/crew_app.py`
- [ ] Verify: Same agent system works via CrewAI

**Step 6.2: MS Agent Framework Adapter**
- [ ] Write tests for: Event-driven agent communication
- [ ] Write tests for: Message routing
- [ ] Write tests for: State synchronization
- [ ] Implement: `adapters/ms_agent_app.py`
- [ ] Verify: Same agent system works via MS framework

### Phase 7: Integration & Polish

**Step 7.1: End-to-End Testing**
- [ ] Write tests for: Complete workflow with all adapters
- [ ] Write tests for: Observability data completeness
- [ ] Write tests for: Error recovery scenarios
- [ ] Implement: Integration test suite
- [ ] Verify: All adapters produce equivalent results

**Step 7.2: Main Entry Point**
- [ ] Write tests for: Adapter selection logic
- [ ] Write tests for: CLI argument parsing
- [ ] Write tests for: Configuration loading
- [ ] Implement: `main.py` orchestrator switcher
- [ ] Verify: All adapters can be selected via CLI

**Step 7.3: Documentation & Examples**
- [ ] Create example marketing plan prompts
- [ ] Document Langfuse Cloud dashboard usage
- [ ] Create troubleshooting guide
- [ ] Add performance tuning tips

---

## Commands Reference

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_observability.py -v

# Run tests with coverage
pytest tests/ --cov=core --cov=adapters --cov-report=html

# Run single test
pytest tests/test_brain.py::test_llm_call_tracing -v
```

### Development
```bash
# Format code
black core/ adapters/ tests/

# Lint code
ruff check core/ adapters/ tests/

# Type check
mypy core/ adapters/
```

### Database
```bash
# Initialize SQLite database
python -c "from core.memory import init_db; init_db()"

# View database contents
sqlite3 data/agents.db "SELECT * FROM conversations;"

# Reset database
rm data/agents.db && python -c "from core.memory import init_db; init_db()"
```

### Running the Application
```bash
# Run with LangGraph adapter
python main.py --adapter langgraph --prompt "Create a marketing plan for a SaaS startup"

# Run with CrewAI adapter
python main.py --adapter crew --prompt "Create a marketing plan for a SaaS startup"

# Run with debug logging
python main.py --adapter langgraph --prompt "..." --debug

# View Langfuse traces
# Open https://cloud.langfuse.com in browser
```
