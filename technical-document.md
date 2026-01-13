Technical Architecture: Framework-Agnostic Agent System
1. Executive Summary
This architecture provides a modular, production-grade foundation for building AI agent systems. It is designed to be framework-agnostic, allowing developers to switch between orchestration libraries (LangGraph, CrewAI, or Microsoft Agent Framework) without rewriting the core business logic. The system prioritizes local-first observability via OpenTelemetry (OTel) and Langfuse, and utilizes OpenRouter as a unified gateway for model flexibility.
2. Core Architecture Decisions
A. Modular Logic Separation
To ensure framework independence, the code is divided into three isolated layers:
The Brain (LLM Logic): Pure Python functions using the standard openai SDK to communicate with OpenRouter.
The Hands (Tools): Framework-independent Python functions with clear type hints and docstrings.
The Glue (Adapters): Minimalist scripts that wrap the "Brain" and "Hands" for specific orchestrators.
B. Observability via OpenTelemetry (OTel)
The system adopts the OTel GenAI Semantic Conventions (2026). By instrumenting the base openai client, we capture standardized traces (including prompts, completion tokens, and tool metadata) regardless of the orchestrator. These traces are routed to a local Langfuse instance for visualization and debugging.
C. Lightweight Infrastructure
Database: PostgreSQL for persistent conversation memory and thread management.
Observability: Langfuse for real-time trace inspection and cost monitoring.
Validation: use Pydantic, default_factory::
3. Project Structure
The repository is organized to separate the "how" from the "what."
/my-agent-system
│
├── .env                  # API keys and local config
│
├── /core                 # THE BUSINESS LOGIC (Stable)
│   ├── brain.py          # Unified OpenAI SDK caller
│   ├── schema.py         # Shared State and Data Models
│   └── tools.py          # Pure Python tool functions
│
├── /adapters             # THE ORCHESTRATION (Swappable)
│   ├── langgraph_app.py  # Graph-based state machine logic
│   ├── crew_app.py      # Role-based agentic logic
│   └── ms_agent_app.py   # Event-driven/Enterprise logic
│
└── main.py               # The Switcher (Application Entry)
4. Use Case: Autonomous Marketing Plan Generator
Use Case Overview
The system generates a comprehensive marketing plan by performing real-time competitor research, synthesizing strategic data, and undergoing an iterative critique loop. Unlike linear prompts, this system loops until specific quality benchmarks are met.
Agent Definitions
The Market Scout (Researcher): Specializes in high-precision web searching. It is triggered by the Planner whenever a "knowledge gap" is identified (e.g., missing competitor pricing).
The Architect (Planner): Synthesizes found data into a marketing strategy. It has the autonomy to pause generation and "callback" the Scout for more data before finalizing a draft.
The Judge (Critic): Evaluates the draft against the user’s original business goals. It provides a detailed "Revision List" and can send the plan back to the Architect for re-drafting.
5. Interaction Logic & Loops
The Information Loop (Scout & Architect)
This loop occurs during the drafting phase. If the Architect encounters a query it cannot answer with existing context, it emits a "Tool Call." The orchestrator routes this to the Scout, who fetches the data and returns it to the Architect. The Architect then resumes drafting from the exact point where it paused.
The Refinement Loop (Architect & Judge)
Once a draft is complete, it is passed to the Judge.
Feedback Signal: If the Judge returns a "REVISION_REQUIRED" status, the flow cycles back to the Architect.
Termination: The process only exits to END when the Judge issues an "APPROVED" status or the session hits a predefined turn limit (e.g., 5 iterations).
6. Implementation Prerequisites
OpenRouter API Key: To access models like Claude 3.5 Sonnet or GPT-4o.
Docker Desktop: To run the local observability and database stack.
Python 3.10+: For core application logic.
Environment Variables: Setup for LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, and LANGFUSE_SECRET_KEY.
