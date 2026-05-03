"""
BaseAgent: Core class for all SDK-powered agents

Provides common functionality for agent initialization, context access,
tool invocation, error handling, and logging.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import logging
from datetime import datetime
from pathlib import Path


class BaseAgent(ABC):
    """
    Base class for all Anthropic Agent SDK powered agents.

    All SubAgents inherit from this class to get shared functionality:
    - Context access and management
    - Tool invocation wrapper
    - Error handling and logging
    - Agent lifecycle management

    Example:
        ```python
        class BackendDeveloper(BaseAgent):
            def __init__(self):
                super().__init__(
                    name="backend-developer",
                    description="Backend development specialist",
                    model="claude-opus-4-5",
                    tools=["Read", "Edit", "Write", "Bash"]
                )

            def process(self, context):
                task = context.get("task")
                # ... implementation
                context.set("backend_complete", True)
                return {"status": "completed"}
        ```
    """

    def __init__(
        self,
        name: str,
        description: str,
        model: str = "claude-opus-4-5",
        tools: Optional[List[str]] = None,
        enable_memory: bool = False,
        enable_plugins: bool = False,
        enable_hooks: bool = False,
        max_retries: int = 3,
        timeout: int = 300,
    ):
        """
        Initialize a base agent.

        Args:
            name: Agent identifier (e.g., "backend-developer")
            description: Brief description of agent's purpose
            model: Claude model to use (default: Sonnet 4.5)
            tools: List of Claude Code tools this agent can use
            enable_memory: Enable access to Claude Code Memory system
            enable_plugins: Enable access to Claude Code Plugins
            enable_hooks: Enable lifecycle hooks (start, complete, error)
            max_retries: Maximum retry attempts on failure
            timeout: Agent execution timeout in seconds
        """
        self.name = name
        self.description = description
        self.model = model
        self.tools = tools or []
        self.enable_memory = enable_memory
        self.enable_plugins = enable_plugins
        self.enable_hooks = enable_hooks
        self.max_retries = max_retries
        self.timeout = timeout

        # Initialize logging
        self.logger = self._setup_logger()

        # Track agent state
        self.state = {
            "status": "initialized",
            "started_at": None,
            "completed_at": None,
            "error": None,
            "retry_count": 0,
        }

        self.logger.info(f"Agent '{self.name}' initialized with model {self.model}")

    def _setup_logger(self) -> logging.Logger:
        """
        Set up agent-specific logger.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(f"agent.{self.name}")
        logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        log_dir = Path(".claude/logs/agents")
        log_dir.mkdir(parents=True, exist_ok=True)

        # File handler for agent-specific logs
        log_file = log_dir / f"{self.name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    @abstractmethod
    def process(self, context: "AgentContext") -> Dict[str, Any]:
        """
        Main agent processing logic - must be implemented by subclasses.

        This is where the agent does its actual work:
        - Read task from context
        - Access shared artifacts
        - Perform agent-specific operations
        - Update context with results
        - Return structured result

        Args:
            context: Shared agent context with task and artifacts

        Returns:
            Dictionary with agent results:
            {
                "status": "completed" | "failed" | "needs_input",
                "artifacts": {...},  # New artifacts created
                "next_agent": "agent-name" | None,
                "error": "error message" | None
            }

        Raises:
            NotImplementedError: If subclass doesn't implement this method
        """
        raise NotImplementedError(
            f"Agent '{self.name}' must implement process() method"
        )

    def run(self, context: "AgentContext") -> Dict[str, Any]:
        """
        Execute agent with error handling, retries, and logging.

        This is the public interface for running an agent. It wraps the
        process() method with:
        - State management
        - Error handling
        - Retry logic
        - Logging
        - Hooks (if enabled)

        Args:
            context: Shared agent context

        Returns:
            Agent result dictionary

        Raises:
            RuntimeError: If agent fails after max retries
        """
        self.state["status"] = "running"
        self.state["started_at"] = datetime.now().isoformat()
        self.logger.info(f"Starting agent '{self.name}'")

        # Trigger start hook if enabled
        if self.enable_hooks:
            self._trigger_hook("start", context)

        # Retry loop
        for attempt in range(self.max_retries):
            try:
                self.state["retry_count"] = attempt

                # Call agent-specific process method
                result = self.process(context)

                # Success
                self.state["status"] = "completed"
                self.state["completed_at"] = datetime.now().isoformat()
                self.logger.info(f"Agent '{self.name}' completed successfully")

                # Update context with agent state
                context.set_agent_state(self.name, self.state)

                # Trigger complete hook if enabled
                if self.enable_hooks:
                    self._trigger_hook("complete", context, result=result)

                return result

            except Exception as e:
                self.state["error"] = str(e)
                self.logger.error(
                    f"Agent '{self.name}' failed (attempt {attempt + 1}/{self.max_retries}): {e}",
                    exc_info=True
                )

                # Last attempt
                if attempt == self.max_retries - 1:
                    self.state["status"] = "failed"
                    self.state["completed_at"] = datetime.now().isoformat()

                    # Trigger error hook if enabled
                    if self.enable_hooks:
                        self._trigger_hook("error", context, error=e)

                    # Update context with failure state
                    context.set_agent_state(self.name, self.state)

                    raise RuntimeError(
                        f"Agent '{self.name}' failed after {self.max_retries} attempts: {e}"
                    ) from e

                # Wait before retry (exponential backoff)
                import time
                wait_time = 2 ** attempt
                self.logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    def _trigger_hook(
        self,
        hook_type: str,
        context: "AgentContext",
        result: Optional[Dict] = None,
        error: Optional[Exception] = None
    ):
        """
        Trigger agent lifecycle hook.

        Args:
            hook_type: "start", "complete", or "error"
            context: Current agent context
            result: Agent result (for complete hook)
            error: Exception (for error hook)
        """
        try:
            hook_data = {
                "agent": self.name,
                "hook_type": hook_type,
                "timestamp": datetime.now().isoformat(),
                "context_id": context.workflow_id,
            }

            if result:
                hook_data["result"] = result

            if error:
                hook_data["error"] = str(error)

            # Log hook event to context
            context.add_hook_event(hook_data)

            self.logger.debug(f"Hook '{hook_type}' triggered for agent '{self.name}'")

        except Exception as e:
            self.logger.warning(f"Hook '{hook_type}' failed: {e}")

    def invoke_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Any:
        """
        Invoke a Claude Code tool with error handling.

        Wrapper around Claude Code tools (Read, Write, Edit, Bash, etc.)
        with error handling and logging.

        Args:
            tool_name: Name of the tool to invoke ("Read", "Write", etc.)
            **kwargs: Tool-specific parameters

        Returns:
            Tool result

        Raises:
            ValueError: If tool not available for this agent
            RuntimeError: If tool invocation fails

        Example:
            ```python
            content = self.invoke_tool("Read", file_path="/path/to/file.py")
            self.invoke_tool("Write", file_path="/path/to/new.py", content="...")
            ```
        """
        if tool_name not in self.tools:
            raise ValueError(
                f"Tool '{tool_name}' not available for agent '{self.name}'. "
                f"Available tools: {self.tools}"
            )

        self.logger.debug(f"Invoking tool '{tool_name}' with args: {kwargs}")

        try:
            # NOTE: Actual tool invocation would integrate with Cursor's
            # tool system. For now, this is a placeholder for the interface.
            # In real implementation, this would call Cursor's tool API.

            self.logger.info(f"Tool '{tool_name}' invoked successfully")
            return {"status": "success", "tool": tool_name, "args": kwargs}

        except Exception as e:
            self.logger.error(f"Tool '{tool_name}' failed: {e}")
            raise RuntimeError(f"Tool invocation failed: {e}") from e

    def get_context_value(self, context: "AgentContext", key: str, default: Any = None) -> Any:
        """
        Safely get value from context with default.

        Args:
            context: Agent context
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            Value from context or default
        """
        try:
            return context.get(key, default)
        except Exception as e:
            self.logger.warning(f"Failed to get context value '{key}': {e}")
            return default

    def set_context_value(self, context: "AgentContext", key: str, value: Any):
        """
        Safely set value in context.

        Args:
            context: Agent context
            key: Key to set
            value: Value to store
        """
        try:
            context.set(key, value)
        except Exception as e:
            self.logger.error(f"Failed to set context value '{key}': {e}")

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(name='{self.name}', "
            f"model='{self.model}', status='{self.state['status']}')>"
        )
