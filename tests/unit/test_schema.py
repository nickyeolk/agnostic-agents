"""
Tests for core schema models.
Tests Pydantic models for messages, agents, conversations, and state.
"""
import pytest
from datetime import datetime
from typing import Dict, Any


class TestMessageModels:
    """Tests for message data models."""

    def test_user_message_creation(self):
        """Test creating a user message."""
        from core.schema import UserMessage

        msg = UserMessage(
            content="Hello, how can you help me?",
            metadata={"source": "cli"}
        )

        assert msg.role == "user"
        assert msg.content == "Hello, how can you help me?"
        assert msg.metadata == {"source": "cli"}
        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, datetime)

    def test_assistant_message_creation(self):
        """Test creating an assistant message."""
        from core.schema import AssistantMessage

        msg = AssistantMessage(
            content="I can help you with various tasks.",
            model="anthropic/claude-3.5-sonnet",
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18
            }
        )

        assert msg.role == "assistant"
        assert msg.content == "I can help you with various tasks."
        assert msg.model == "anthropic/claude-3.5-sonnet"
        assert msg.usage["prompt_tokens"] == 10
        assert msg.usage["completion_tokens"] == 8
        assert msg.timestamp is not None

    def test_tool_message_creation(self):
        """Test creating a tool call and result message."""
        from core.schema import ToolCallMessage, ToolResultMessage

        # Tool call
        call = ToolCallMessage(
            tool_name="web_search",
            arguments={"query": "latest AI news"},
            call_id="call_123"
        )

        assert call.role == "tool_call"
        assert call.tool_name == "web_search"
        assert call.arguments == {"query": "latest AI news"}
        assert call.call_id == "call_123"

        # Tool result
        result = ToolResultMessage(
            tool_name="web_search",
            result={"articles": ["article1", "article2"]},
            call_id="call_123",
            success=True
        )

        assert result.role == "tool_result"
        assert result.tool_name == "web_search"
        assert result.result == {"articles": ["article1", "article2"]}
        assert result.success is True

    def test_message_with_default_timestamp(self):
        """Test that messages get automatic timestamps."""
        from core.schema import UserMessage
        import time

        msg1 = UserMessage(content="First message")
        time.sleep(0.01)
        msg2 = UserMessage(content="Second message")

        assert msg1.timestamp < msg2.timestamp

    def test_message_serialization(self):
        """Test that messages can be serialized to dict."""
        from core.schema import AssistantMessage

        msg = AssistantMessage(
            content="Test content",
            model="test-model"
        )

        # Should be able to convert to dict (Pydantic v1 uses dict(), v2 uses model_dump())
        msg_dict = msg.dict() if hasattr(msg, 'dict') else msg.model_dump()
        assert msg_dict["role"] == "assistant"
        assert msg_dict["content"] == "Test content"
        assert msg_dict["model"] == "test-model"


class TestAgentRolesAndStatus:
    """Tests for agent role enums and status types."""

    def test_agent_role_enum(self):
        """Test agent role enumeration."""
        from core.schema import AgentRole

        assert AgentRole.SCOUT == "scout"
        assert AgentRole.ARCHITECT == "architect"
        assert AgentRole.JUDGE == "judge"

    def test_agent_status_enum(self):
        """Test agent status enumeration."""
        from core.schema import AgentStatus

        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.WORKING == "working"
        assert AgentStatus.COMPLETED == "completed"
        assert AgentStatus.ERROR == "error"

    def test_agent_state_model(self):
        """Test agent state tracking model."""
        from core.schema import AgentState, AgentRole, AgentStatus

        state = AgentState(
            role=AgentRole.SCOUT,
            status=AgentStatus.WORKING,
            current_task="Searching for competitor information",
            metadata={"query": "competitor pricing"}
        )

        assert state.role == AgentRole.SCOUT
        assert state.status == AgentStatus.WORKING
        assert state.current_task == "Searching for competitor information"
        assert state.metadata["query"] == "competitor pricing"

    def test_revision_status_enum(self):
        """Test revision status for judge evaluations."""
        from core.schema import RevisionStatus

        assert RevisionStatus.APPROVED == "approved"
        assert RevisionStatus.REVISION_REQUIRED == "revision_required"


class TestConversationModels:
    """Tests for conversation and thread models."""

    def test_conversation_thread_creation(self):
        """Test creating a conversation thread."""
        from core.schema import ConversationThread, UserMessage

        thread = ConversationThread(
            thread_id="thread_123",
            user_id="user_456",
            metadata={"purpose": "marketing_plan"}
        )

        assert thread.thread_id == "thread_123"
        assert thread.user_id == "user_456"
        assert thread.messages == []
        assert thread.metadata["purpose"] == "marketing_plan"
        assert thread.created_at is not None

    def test_adding_messages_to_thread(self):
        """Test adding messages to a conversation thread."""
        from core.schema import ConversationThread, UserMessage, AssistantMessage

        thread = ConversationThread(
            thread_id="thread_123",
            user_id="user_456"
        )

        # Add user message
        user_msg = UserMessage(content="Hello")
        thread.messages.append(user_msg)

        # Add assistant message
        assistant_msg = AssistantMessage(
            content="Hi there!",
            model="test-model"
        )
        thread.messages.append(assistant_msg)

        assert len(thread.messages) == 2
        assert thread.messages[0].role == "user"
        assert thread.messages[1].role == "assistant"

    def test_thread_message_count(self):
        """Test getting message count from thread."""
        from core.schema import ConversationThread, UserMessage

        thread = ConversationThread(thread_id="test")

        assert len(thread.messages) == 0

        thread.messages.append(UserMessage(content="msg1"))
        thread.messages.append(UserMessage(content="msg2"))

        assert len(thread.messages) == 2


class TestStateModels:
    """Tests for agent system state models."""

    def test_agent_system_state(self):
        """Test overall agent system state."""
        from core.schema import AgentSystemState, AgentRole, AgentStatus, AgentState

        scout_state = AgentState(
            role=AgentRole.SCOUT,
            status=AgentStatus.IDLE
        )

        architect_state = AgentState(
            role=AgentRole.ARCHITECT,
            status=AgentStatus.WORKING,
            current_task="Generating marketing plan"
        )

        system_state = AgentSystemState(
            agents={
                AgentRole.SCOUT: scout_state,
                AgentRole.ARCHITECT: architect_state
            },
            current_iteration=1,
            max_iterations=5,
            metadata={"session": "session_123"}
        )

        assert len(system_state.agents) == 2
        assert system_state.agents[AgentRole.SCOUT].status == AgentStatus.IDLE
        assert system_state.agents[AgentRole.ARCHITECT].status == AgentStatus.WORKING
        assert system_state.current_iteration == 1
        assert system_state.max_iterations == 5

    def test_draft_evaluation_model(self):
        """Test draft evaluation from judge."""
        from core.schema import DraftEvaluation, RevisionStatus

        evaluation = DraftEvaluation(
            status=RevisionStatus.REVISION_REQUIRED,
            feedback="The competitive analysis section needs more depth.",
            score=6.5,
            revision_notes=[
                "Add more competitor pricing details",
                "Include market share analysis"
            ]
        )

        assert evaluation.status == RevisionStatus.REVISION_REQUIRED
        assert evaluation.feedback == "The competitive analysis section needs more depth."
        assert evaluation.score == 6.5
        assert len(evaluation.revision_notes) == 2

    def test_approved_evaluation(self):
        """Test approved draft evaluation."""
        from core.schema import DraftEvaluation, RevisionStatus

        evaluation = DraftEvaluation(
            status=RevisionStatus.APPROVED,
            feedback="Excellent work! All requirements met.",
            score=9.5,
            revision_notes=[]
        )

        assert evaluation.status == RevisionStatus.APPROVED
        assert evaluation.score == 9.5
        assert len(evaluation.revision_notes) == 0


class TestModelValidation:
    """Tests for Pydantic validation and edge cases."""

    def test_message_requires_content(self):
        """Test that messages require content."""
        from core.schema import UserMessage

        with pytest.raises(Exception):  # Pydantic ValidationError
            UserMessage()  # Missing required content

    def test_tool_call_requires_name_and_args(self):
        """Test that tool calls require name and arguments."""
        from core.schema import ToolCallMessage

        with pytest.raises(Exception):  # Pydantic ValidationError
            ToolCallMessage(tool_name="search")  # Missing arguments

    def test_usage_dict_structure(self):
        """Test that usage dict has correct structure."""
        from core.schema import AssistantMessage

        msg = AssistantMessage(
            content="Test",
            model="test-model",
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        )

        assert "prompt_tokens" in msg.usage
        assert "completion_tokens" in msg.usage
        assert "total_tokens" in msg.usage

    def test_empty_metadata_allowed(self):
        """Test that metadata can be empty or None."""
        from core.schema import UserMessage

        msg1 = UserMessage(content="Test")
        msg2 = UserMessage(content="Test", metadata={})

        assert msg1.metadata == {}
        assert msg2.metadata == {}
