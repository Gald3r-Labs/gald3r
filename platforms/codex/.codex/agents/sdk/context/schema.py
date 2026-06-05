"""
Context Schema for Hybrid Agent System

Defines the shared context structure for SDK and prompt-based agents.
Supports context passing, persistence, and versioning.

Author: Database Expert Agent
Date: 2025-11-01
Task: 052 - Anthropic Agent SDK Integration
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class AgentMode(str, Enum):
    """Agent execution mode"""
    SDK = "sdk"
    PROMPT_BASED = "prompt-based"
    HYBRID = "hybrid"


class AgentStatus(str, Enum):
    """Agent execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class HookEvent(BaseModel):
    """Hook event record"""
    event: str = Field(..., description="Hook event name (agent-start, agent-complete, agent-error)")
    agent: str = Field(..., description="Agent name that triggered the event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: Optional[bool] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CommandExecution(BaseModel):
    """Command execution record"""
    command: str = Field(..., description="Command name (e.g., /review-pr)")
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True


class FallbackLog(BaseModel):
    """Fallback event log"""
    agent: str = Field(..., description="Agent that triggered fallback")
    reason: str = Field(..., description="Reason for fallback")
    fallback_to: str = Field(..., description="Fallback target (prompt-based, etc)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = False


class AgentState(BaseModel):
    """Individual agent state within workflow"""
    status: AgentStatus = AgentStatus.PENDING
    agent_type: AgentMode = AgentMode.SDK
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0

    # Agent-specific results
    files_created: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    tests_passing: Optional[bool] = None

    # Primitives usage tracking
    memory_accessed: List[str] = Field(default_factory=list, description="Memory keys accessed")
    plugins_called: List[str] = Field(default_factory=list, description="Plugins invoked")
    commands_executed: List[str] = Field(default_factory=list, description="Slash commands executed")
    hooks_triggered: List[str] = Field(default_factory=list, description="Hooks triggered")

    # Custom agent data
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class SharedArtifacts(BaseModel):
    """Shared artifacts between agents"""
    database_schema: Optional[Dict[str, Any]] = None
    api_endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    implementation_files: List[str] = Field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None
    plugin_results: Dict[str, Any] = Field(default_factory=dict)

    # Allow arbitrary additional artifacts
    custom: Dict[str, Any] = Field(default_factory=dict)


class MemoryContext(BaseModel):
    """Memory system integration"""
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    workflow_history: List[Dict[str, Any]] = Field(default_factory=list)
    agent_learnings: Dict[str, Any] = Field(default_factory=dict)
    project_patterns: Dict[str, Any] = Field(default_factory=dict)


class WorkflowMetadata(BaseModel):
    """Workflow metadata"""
    user_id: Optional[str] = None
    project_path: str
    priority: str = "medium"

    # Context storage locations
    sdk_context_file: Optional[str] = None
    json_context_file: Optional[str] = None

    # Workflow classification
    workflow_type: Optional[str] = None  # "fullstack_feature", "database_migration", etc
    tags: List[str] = Field(default_factory=list)

    # TTL and archiving
    ttl_hours: int = 72  # Default 3 days
    archived: bool = False
    archived_at: Optional[datetime] = None


class AgentContext(BaseModel):
    """
    Unified context for hybrid agent workflows

    This context structure supports:
    - SDK-based agents (structured context passing)
    - Prompt-based agents (via JSON serialization)
    - Memory system integration
    - Plugin/Command/Hook tracking
    - Fallback mechanisms
    - Context persistence and archiving
    """

    # Core workflow identity
    workflow_id: UUID = Field(default_factory=uuid4)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Task definition
    task: str = Field(..., description="Task description")
    phase: str = Field(default="planning", description="Current workflow phase")
    agent_mode: AgentMode = AgentMode.HYBRID

    # Agent tracking
    agents_completed: List[str] = Field(default_factory=list)
    current_agent: Optional[str] = None
    next_agent: Optional[str] = None

    # Shared state
    shared_artifacts: SharedArtifacts = Field(default_factory=SharedArtifacts)
    agent_states: Dict[str, AgentState] = Field(default_factory=dict)

    # Primitives integration
    memory_context: MemoryContext = Field(default_factory=MemoryContext)
    hook_events: List[HookEvent] = Field(default_factory=list)
    commands_executed: List[CommandExecution] = Field(default_factory=list)

    # Fallback tracking
    fallback_log: List[FallbackLog] = Field(default_factory=list)

    # Metadata
    metadata: WorkflowMetadata

    # Version control
    version: int = Field(default=1, description="Context schema version")

    @field_validator('workflow_id', mode='before')
    @classmethod
    def convert_workflow_id(cls, v):
        """Convert string UUID to UUID object"""
        if isinstance(v, str):
            return UUID(v)
        return v

    def model_dump_json_safe(self) -> Dict[str, Any]:
        """
        Dump model to JSON-safe dict (for prompt-based agents)
        Converts UUIDs and datetimes to strings
        """
        data = self.model_dump()

        # Convert UUID to string
        data['workflow_id'] = str(data['workflow_id'])

        # Convert datetimes to ISO format
        for key in ['started_at', 'updated_at', 'completed_at']:
            if data.get(key):
                data[key] = data[key].isoformat() if isinstance(data[key], datetime) else data[key]

        # Convert hook event timestamps
        for event in data.get('hook_events', []):
            if event.get('timestamp'):
                event['timestamp'] = event['timestamp'].isoformat() if isinstance(event['timestamp'], datetime) else event['timestamp']

        # Convert command execution timestamps
        for cmd in data.get('commands_executed', []):
            if cmd.get('timestamp'):
                cmd['timestamp'] = cmd['timestamp'].isoformat() if isinstance(cmd['timestamp'], datetime) else cmd['timestamp']

        # Convert fallback log timestamps
        for fb in data.get('fallback_log', []):
            if fb.get('timestamp'):
                fb['timestamp'] = fb['timestamp'].isoformat() if isinstance(fb['timestamp'], datetime) else fb['timestamp']

        # Convert agent state timestamps
        for agent_name, state in data.get('agent_states', {}).items():
            for key in ['started_at', 'completed_at']:
                if state.get(key):
                    state[key] = state[key].isoformat() if isinstance(state[key], datetime) else state[key]

        return data

    def get_agent_state(self, agent_name: str) -> AgentState:
        """Get or create agent state"""
        if agent_name not in self.agent_states:
            self.agent_states[agent_name] = AgentState()
        return self.agent_states[agent_name]

    def mark_agent_started(self, agent_name: str, agent_type: AgentMode = AgentMode.SDK):
        """Mark agent as started"""
        state = self.get_agent_state(agent_name)
        state.status = AgentStatus.IN_PROGRESS
        state.agent_type = agent_type
        state.started_at = datetime.utcnow()
        self.current_agent = agent_name
        self.updated_at = datetime.utcnow()

    def mark_agent_completed(self, agent_name: str):
        """Mark agent as completed"""
        state = self.get_agent_state(agent_name)
        state.status = AgentStatus.COMPLETED
        state.completed_at = datetime.utcnow()

        if agent_name not in self.agents_completed:
            self.agents_completed.append(agent_name)

        self.current_agent = None
        self.updated_at = datetime.utcnow()

    def mark_agent_failed(self, agent_name: str, error: str):
        """Mark agent as failed"""
        state = self.get_agent_state(agent_name)
        state.status = AgentStatus.FAILED
        state.error = error
        state.completed_at = datetime.utcnow()
        self.current_agent = None
        self.updated_at = datetime.utcnow()

    def add_hook_event(self, event: str, agent: str, success: Optional[bool] = None, metadata: Optional[Dict] = None):
        """Add hook event to log"""
        hook = HookEvent(
            event=event,
            agent=agent,
            success=success,
            metadata=metadata or {}
        )
        self.hook_events.append(hook)
        self.updated_at = datetime.utcnow()

    def add_command_execution(self, command: str, arguments: Dict[str, Any], result: Optional[Dict] = None, success: bool = True):
        """Add command execution to log"""
        cmd = CommandExecution(
            command=command,
            arguments=arguments,
            result=result,
            success=success
        )
        self.commands_executed.append(cmd)
        self.updated_at = datetime.utcnow()

    def add_fallback(self, agent: str, reason: str, fallback_to: str, success: bool = False):
        """Add fallback event to log"""
        fallback = FallbackLog(
            agent=agent,
            reason=reason,
            fallback_to=fallback_to,
            success=success
        )
        self.fallback_log.append(fallback)
        self.updated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if context has exceeded TTL"""
        from datetime import timedelta
        ttl = timedelta(hours=self.metadata.ttl_hours)
        return (datetime.utcnow() - self.started_at) > ttl

    def mark_completed(self):
        """Mark workflow as completed"""
        self.completed_at = datetime.utcnow()
        self.current_agent = None
        self.updated_at = datetime.utcnow()


# Example usage and validation
if __name__ == "__main__":
    # Create example context
    context = AgentContext(
        task="Implement user authentication system",
        metadata=WorkflowMetadata(
            project_path="/mnt/c/git/myproject",
            priority="high",
            workflow_type="fullstack_feature",
            tags=["auth", "security"]
        )
    )

    # Mark agent started
    context.mark_agent_started("backend-developer", AgentMode.SDK)

    # Add hook event
    context.add_hook_event("agent-start", "backend-developer", success=True)

    # Update agent state
    state = context.get_agent_state("backend-developer")
    state.files_created = ["src/auth/login.ts", "src/auth/logout.ts"]
    state.plugins_called = ["mcp__brave_search"]
    state.memory_accessed = ["database_preference"]

    # Add shared artifacts
    context.shared_artifacts.api_endpoints = [
        {"path": "/api/auth/login", "method": "POST", "file": "src/auth/login.ts"},
        {"path": "/api/auth/logout", "method": "POST", "file": "src/auth/logout.ts"}
    ]

    # Mark completed
    context.mark_agent_completed("backend-developer")

    # Print JSON-safe version
    import json
    print(json.dumps(context.model_dump_json_safe(), indent=2))

    print("\n✅ Context schema validated successfully!")
