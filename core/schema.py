"""
Core schema models for the agent system.
Defines Pydantic models for messages, agents, conversations, and state.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class AgentRole(str, Enum):
    """Agent roles in the system."""
    SCOUT = "scout"
    ARCHITECT = "architect"
    JUDGE = "judge"


class AgentStatus(str, Enum):
    """Status of an agent."""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"


class RevisionStatus(str, Enum):
    """Status of draft evaluation."""
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"


# ============================================================================
# Message Models
# ============================================================================

class BaseMessage(BaseModel):
    """Base message model."""
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class UserMessage(BaseMessage):
    """Message from the user."""
    role: str = "user"


class AssistantMessage(BaseMessage):
    """Message from the assistant/agent."""
    role: str = "assistant"
    model: str
    usage: Optional[Dict[str, int]] = None


class ToolCallMessage(BaseModel):
    """Message representing a tool call."""
    role: str = "tool_call"
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolResultMessage(BaseModel):
    """Message representing a tool result."""
    role: str = "tool_result"
    tool_name: str
    result: Any
    call_id: str
    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Union type for all message types
Message = Union[UserMessage, AssistantMessage, ToolCallMessage, ToolResultMessage]


# ============================================================================
# Agent Models
# ============================================================================

class AgentState(BaseModel):
    """State of a single agent."""
    role: AgentRole
    status: AgentStatus
    current_task: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class DraftEvaluation(BaseModel):
    """Evaluation of a draft by the judge agent."""
    status: RevisionStatus
    feedback: str
    score: float
    revision_notes: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


# ============================================================================
# Conversation Models
# ============================================================================

class ConversationThread(BaseModel):
    """A conversation thread with message history."""
    thread_id: str
    user_id: Optional[str] = None
    messages: List[Union[UserMessage, AssistantMessage, ToolCallMessage, ToolResultMessage]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# System State Models
# ============================================================================

class AgentSystemState(BaseModel):
    """Overall state of the agent system."""
    agents: Dict[AgentRole, AgentState]
    current_iteration: int = 0
    max_iterations: int = 5
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True
