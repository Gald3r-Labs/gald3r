"""
AgentContext: Shared context for agent-to-agent communication

Manages shared state, artifacts, and data passing between agents.
Supports JSON serialization, validation, versioning, and persistence.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
import logging


class ContextMetadata(BaseModel):
    """Metadata for agent context"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: int = Field(default=1)
    ttl_hours: Optional[int] = Field(default=24)
    user_id: Optional[str] = None
    project_path: Optional[str] = None
    priority: str = Field(default="medium")

    @validator('priority')
    def validate_priority(cls, v):
        allowed = ['low', 'medium', 'high', 'critical']
        if v not in allowed:
            raise ValueError(f"Priority must be one of {allowed}")
        return v


class AgentContext:
    """
    Shared context for agent collaboration with structured data passing.

    Provides:
    - Get/set methods for shared data
    - Agent state tracking
    - JSON serialization/deserialization
    - Pydantic validation
    - Context versioning
    - TTL and cleanup
    - Persistence to disk

    Example:
        ```python
        # Create context
        context = AgentContext(task="Build user authentication")

        # Agent 1: Database Expert
        context.set("database_schema", {"tables": ["users", "sessions"]})
        context.set("migrations", ["001_create_users.sql"])

        # Agent 2: Backend Developer (reads database schema)
        schema = context.get("database_schema")
        # ... implement API using schema
        context.set("api_endpoints", ["/api/auth/login", "/api/auth/logout"])

        # Agent 3: Frontend Developer (reads API endpoints)
        endpoints = context.get("api_endpoints")
        # ... build UI calling these endpoints

        # Save context to disk
        context.save()

        # Later, restore context
        restored = AgentContext.load(context.workflow_id)
        ```
    """

    def __init__(
        self,
        task: Optional[str] = None,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_path: Optional[str] = None,
        priority: str = "medium",
        ttl_hours: int = 24,
        initial_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent context.

        Args:
            task: Task description for this workflow
            workflow_id: Unique workflow identifier (auto-generated if None)
            user_id: User who initiated this workflow
            project_path: Absolute path to project directory
            priority: Workflow priority (low, medium, high, critical)
            ttl_hours: Time-to-live in hours before cleanup
            initial_data: Initial context data
        """
        # Metadata
        self.metadata = ContextMetadata(
            workflow_id=workflow_id or str(uuid.uuid4()),
            user_id=user_id,
            project_path=project_path or str(Path.cwd()),
            priority=priority,
            ttl_hours=ttl_hours
        )

        # Core data
        self.task = task
        self.phase = "planning"
        self.agents_completed: List[str] = []
        self.current_agent: Optional[str] = None

        # Shared artifacts (data passed between agents)
        self.shared_artifacts: Dict[str, Any] = initial_data or {}

        # Agent states (track each agent's progress)
        self.agent_states: Dict[str, Dict[str, Any]] = {}

        # Hook events log
        self.hook_events: List[Dict[str, Any]] = []

        # Fallback log (track SDK -> prompt-based fallbacks)
        self.fallback_log: List[Dict[str, Any]] = []

        # Setup logging
        self.logger = logging.getLogger(f"context.{self.workflow_id}")
        self.logger.setLevel(logging.INFO)

    @property
    def workflow_id(self) -> str:
        """Get workflow ID"""
        return self.metadata.workflow_id

    @property
    def version(self) -> int:
        """Get context version"""
        return self.metadata.version

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from shared artifacts.

        Args:
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            Value from context or default
        """
        return self.shared_artifacts.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set value in shared artifacts.

        Args:
            key: Key to set
            value: Value to store
        """
        self.shared_artifacts[key] = value
        self._update_timestamp()
        self.logger.debug(f"Set context key '{key}'")

    def update(self, data: Dict[str, Any]):
        """
        Update multiple values at once.

        Args:
            data: Dictionary of key-value pairs to update
        """
        self.shared_artifacts.update(data)
        self._update_timestamp()
        self.logger.debug(f"Updated context with {len(data)} keys")

    def delete(self, key: str):
        """
        Delete key from shared artifacts.

        Args:
            key: Key to delete
        """
        if key in self.shared_artifacts:
            del self.shared_artifacts[key]
            self._update_timestamp()
            self.logger.debug(f"Deleted context key '{key}'")

    def get_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get state for specific agent.

        Args:
            agent_name: Name of agent

        Returns:
            Agent state dictionary or None
        """
        return self.agent_states.get(agent_name)

    def set_agent_state(self, agent_name: str, state: Dict[str, Any]):
        """
        Set state for specific agent.

        Args:
            agent_name: Name of agent
            state: Agent state dictionary
        """
        self.agent_states[agent_name] = state
        self._update_timestamp()

        # Track completed agents
        if state.get("status") == "completed" and agent_name not in self.agents_completed:
            self.agents_completed.append(agent_name)

        self.logger.info(f"Updated state for agent '{agent_name}'")

    def add_hook_event(self, event: Dict[str, Any]):
        """
        Add hook event to log.

        Args:
            event: Hook event data
        """
        event["timestamp"] = event.get("timestamp", datetime.now().isoformat())
        self.hook_events.append(event)
        self._update_timestamp()

    def add_fallback(self, agent: str, reason: str, fallback_to: str):
        """
        Log fallback from SDK to prompt-based agent.

        Args:
            agent: Agent name that failed
            reason: Reason for fallback
            fallback_to: Type of fallback (e.g., "prompt-based")
        """
        fallback_entry = {
            "agent": agent,
            "reason": reason,
            "fallback_to": fallback_to,
            "timestamp": datetime.now().isoformat()
        }
        self.fallback_log.append(fallback_entry)
        self.logger.warning(f"Fallback triggered for agent '{agent}': {reason}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary for serialization.

        Returns:
            Dictionary representation of context
        """
        return {
            "metadata": self.metadata.dict(),
            "task": self.task,
            "phase": self.phase,
            "agents_completed": self.agents_completed,
            "current_agent": self.current_agent,
            "shared_artifacts": self.shared_artifacts,
            "agent_states": self.agent_states,
            "hook_events": self.hook_events,
            "fallback_log": self.fallback_log,
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Convert context to JSON string.

        Args:
            indent: JSON indentation (default: 2)

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentContext":
        """
        Create context from dictionary.

        Args:
            data: Dictionary with context data

        Returns:
            AgentContext instance
        """
        metadata = ContextMetadata(**data.get("metadata", {}))

        context = cls(
            task=data.get("task"),
            workflow_id=metadata.workflow_id,
            user_id=metadata.user_id,
            project_path=metadata.project_path,
            priority=metadata.priority,
            ttl_hours=metadata.ttl_hours,
            initial_data=data.get("shared_artifacts", {})
        )

        # Restore state
        context.metadata = metadata
        context.phase = data.get("phase", "planning")
        context.agents_completed = data.get("agents_completed", [])
        context.current_agent = data.get("current_agent")
        context.agent_states = data.get("agent_states", {})
        context.hook_events = data.get("hook_events", [])
        context.fallback_log = data.get("fallback_log", [])

        return context

    @classmethod
    def from_json(cls, json_str: str) -> "AgentContext":
        """
        Create context from JSON string.

        Args:
            json_str: JSON string with context data

        Returns:
            AgentContext instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, context_dir: Optional[Path] = None) -> Path:
        """
        Save context to disk as JSON.

        Args:
            context_dir: Directory to save context (default: .claude/agent_context/active)

        Returns:
            Path to saved context file
        """
        if context_dir is None:
            context_dir = Path(".claude/agent_context/active")

        context_dir.mkdir(parents=True, exist_ok=True)

        context_file = context_dir / f"{self.workflow_id}.json"

        with open(context_file, 'w') as f:
            f.write(self.to_json())

        self.logger.info(f"Context saved to {context_file}")
        return context_file

    @classmethod
    def load(cls, workflow_id: str, context_dir: Optional[Path] = None) -> "AgentContext":
        """
        Load context from disk.

        Args:
            workflow_id: Workflow ID to load
            context_dir: Directory to load from (default: .claude/agent_context/active)

        Returns:
            AgentContext instance

        Raises:
            FileNotFoundError: If context file not found
        """
        if context_dir is None:
            context_dir = Path(".claude/agent_context/active")

        context_file = context_dir / f"{workflow_id}.json"

        if not context_file.exists():
            raise FileNotFoundError(f"Context file not found: {context_file}")

        with open(context_file, 'r') as f:
            json_str = f.read()

        return cls.from_json(json_str)

    def archive(self) -> Path:
        """
        Archive completed context (move from active to archived).

        Returns:
            Path to archived context file
        """
        # Save to archived directory
        archive_dir = Path(".claude/agent_context/archived")
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Add completion timestamp
        self.shared_artifacts["archived_at"] = datetime.now().isoformat()

        archive_file = archive_dir / f"{self.workflow_id}.json"

        with open(archive_file, 'w') as f:
            f.write(self.to_json())

        # Delete from active directory
        active_file = Path(".claude/agent_context/active") / f"{self.workflow_id}.json"
        if active_file.exists():
            active_file.unlink()

        self.logger.info(f"Context archived to {archive_file}")
        return archive_file

    def is_expired(self) -> bool:
        """
        Check if context has exceeded TTL.

        Returns:
            True if expired, False otherwise
        """
        if self.metadata.ttl_hours is None:
            return False

        created_at = datetime.fromisoformat(self.metadata.created_at)
        ttl = timedelta(hours=self.metadata.ttl_hours)
        expiry_time = created_at + ttl

        return datetime.now() > expiry_time

    @classmethod
    def cleanup_expired(cls, context_dir: Optional[Path] = None):
        """
        Clean up expired contexts.

        Args:
            context_dir: Directory to clean (default: .claude/agent_context/active)
        """
        if context_dir is None:
            context_dir = Path(".claude/agent_context/active")

        if not context_dir.exists():
            return

        logger = logging.getLogger("context.cleanup")

        for context_file in context_dir.glob("*.json"):
            try:
                with open(context_file, 'r') as f:
                    data = json.load(f)

                # Create temporary context to check expiry
                context = cls.from_dict(data)

                if context.is_expired():
                    logger.info(f"Archiving expired context: {context.workflow_id}")
                    context.archive()

            except Exception as e:
                logger.error(f"Failed to process context file {context_file}: {e}")

    def _update_timestamp(self):
        """Update the updated_at timestamp"""
        self.metadata.updated_at = datetime.now().isoformat()
        self.metadata.version += 1

    def __repr__(self) -> str:
        return (
            f"<AgentContext(workflow_id='{self.workflow_id}', "
            f"task='{self.task}', phase='{self.phase}', "
            f"version={self.version}, "
            f"agents_completed={len(self.agents_completed)})>"
        )
