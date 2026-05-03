"""
Hooks Integration for Agent SDK

Triggers lifecycle hooks for agent events (start, complete, error).
Integrates with Claude Code's .claude/hooks/ system.

Example:
    hooks = Hooks(agent_name="backend-developer")

    # Trigger agent start
    hooks.trigger("agent-start", context={"task": "Build API"})

    # Trigger agent completion
    hooks.trigger("agent-complete", context=context, result=result)

    # Trigger agent error
    hooks.trigger("agent-error", context=context, error=error)
"""

import json
import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime


class Hooks:
    """
    Claude Code Hooks integration for Agent SDK

    Triggers lifecycle hooks for agent events. Hooks can be used for:
    - Validation (ensure agent prerequisites)
    - Logging (track agent execution)
    - Notifications (alert on completion/errors)
    - Custom workflows (chain additional actions)
    """

    # Supported hook events
    EVENTS = ["agent-start", "agent-complete", "agent-error"]

    def __init__(self, agent_name: str, hooks_dir: str = ".claude/hooks"):
        """
        Initialize Hooks integration

        Args:
            agent_name: Name of the agent
            hooks_dir: Directory containing hook scripts
        """
        self.agent_name = agent_name
        self.hooks_dir = Path(hooks_dir)
        self.event_log = []

        # Create hooks directory if it doesn't exist
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

    def trigger(self, event: str, **data) -> Dict[str, Any]:
        """
        Trigger a hook event

        Args:
            event: Event name ("agent-start", "agent-complete", "agent-error")
            **data: Event data (context, result, error, etc.)

        Returns:
            Hook execution result

        Example:
            hooks.trigger("agent-start", context={"task": "Build API"})
            hooks.trigger("agent-complete", context=context, result=result)
            hooks.trigger("agent-error", context=context, error=error)
        """
        if event not in self.EVENTS:
            return {
                "status": "error",
                "event": event,
                "error": f"Unknown event: {event}. Supported: {self.EVENTS}",
                "timestamp": self._get_timestamp()
            }

        try:
            # Prepare event data
            event_data = {
                "event": event,
                "agent": self.agent_name,
                "timestamp": self._get_timestamp(),
                **data
            }

            # Execute hook script if exists
            hook_result = self._execute_hook(event, event_data)

            # Log event
            log_entry = {
                "event": event,
                "agent": self.agent_name,
                "data": event_data,
                "hook_result": hook_result,
                "timestamp": self._get_timestamp()
            }
            self.event_log.append(log_entry)

            return {
                "status": "success",
                "event": event,
                "hook_result": hook_result,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            error_result = {
                "status": "error",
                "event": event,
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
            self.event_log.append(error_result)
            return error_result

    def get_event_log(self) -> List[Dict[str, Any]]:
        """
        Get log of all triggered events

        Returns:
            List of event records
        """
        return self.event_log

    def clear_event_log(self):
        """Clear event log"""
        self.event_log.clear()

    def _execute_hook(self, event: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute hook script for event

        Args:
            event: Event name
            event_data: Event data to pass to hook

        Returns:
            Hook execution result
        """
        # Look for hook script
        hook_script = self.hooks_dir / f"{event}.sh"

        if not hook_script.exists():
            return {
                "executed": False,
                "reason": f"Hook script not found: {hook_script}"
            }

        try:
            # Convert event data to JSON
            event_json = json.dumps(event_data, indent=2)

            # Execute hook script with event data as stdin
            # NOTE: In production, this would use proper subprocess execution
            # with timeout and error handling
            result = subprocess.run(
                [str(hook_script)],
                input=event_json,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            return {
                "executed": True,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "executed": True,
                "error": "Hook script timeout (30s)"
            }
        except Exception as e:
            return {
                "executed": True,
                "error": str(e)
            }

    def create_hook_template(self, event: str, content: Optional[str] = None):
        """
        Create a hook script template

        Args:
            event: Event name
            content: Optional custom script content
        """
        hook_script = self.hooks_dir / f"{event}.sh"

        if content is None:
            content = self._get_default_hook_template(event)

        with open(hook_script, 'w') as f:
            f.write(content)

        # Make executable
        hook_script.chmod(0o755)

    def _get_default_hook_template(self, event: str) -> str:
        """
        Get default hook script template

        Args:
            event: Event name

        Returns:
            Default script content
        """
        return f"""#!/bin/bash
# {event} hook for agent: {self.agent_name}
# Event data is passed as JSON via stdin

# Read event data
EVENT_DATA=$(cat)

# Log event
echo "[{event}] Agent: {self.agent_name}"
echo "[{event}] Event data: $EVENT_DATA"

# Add your custom logic here
# Examples:
# - Validate prerequisites
# - Send notifications
# - Update external systems
# - Trigger additional workflows

# Exit with 0 for success, non-zero for failure
exit 0
"""

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"


# Example usage
if __name__ == "__main__":
    # Create hooks instance
    hooks = Hooks(agent_name="backend-developer")

    # Trigger agent start
    start_result = hooks.trigger(
        "agent-start",
        context={"task": "Build authentication API"}
    )
    print(f"Start hook result: {json.dumps(start_result, indent=2)}")

    # Trigger agent completion
    complete_result = hooks.trigger(
        "agent-complete",
        context={"task": "Build authentication API"},
        result={"status": "success", "files_created": 5}
    )
    print(f"Complete hook result: {json.dumps(complete_result, indent=2)}")

    # Get event log
    event_log = hooks.get_event_log()
    print(f"Event log: {json.dumps(event_log, indent=2)}")

    # Create hook templates
    for event in Hooks.EVENTS:
        hooks.create_hook_template(event)
    print(f"Hook templates created in {hooks.hooks_dir}")
