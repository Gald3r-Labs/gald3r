"""
Commands Integration for Agent SDK

Enables SDK agents to execute slash commands programmatically.
Results are captured and can be stored in agent context.

Example:
    commands = Commands()

    # Execute a command
    result = commands.execute("/review-pr", pr_number=123)

    # Execute with arguments
    result = commands.execute("/status", format="json")

    # Get execution history
    history = commands.get_history()
"""

import json
import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime


class Commands:
    """
    Cursor Slash Commands integration for Agent SDK

    Allows agents to invoke slash commands programmatically and receive
    structured results.
    """

    def __init__(self, commands_dir: str = ".cursor/commands", context: Optional[Dict[str, Any]] = None):
        """
        Initialize Commands integration

        Args:
            commands_dir: Directory containing command definitions
            context: Optional agent context to store command results
        """
        self.commands_dir = Path(commands_dir)
        self.context = context or {}
        self.execution_history = []

    def execute(self, command_name: str, **args) -> Dict[str, Any]:
        """
        Execute a slash command

        Args:
            command_name: Command to execute (e.g., "/review-pr" or "review-pr")
            **args: Command-specific arguments

        Returns:
            Command execution result

        Example:
            result = commands.execute("/review-pr", pr_number=123)
            result = commands.execute("/status", format="json")
        """
        # Normalize command name (remove leading slash if present)
        cmd_name = command_name.lstrip('/')

        try:
            # Get command definition
            cmd_file = self.commands_dir / f"{cmd_name}.md"

            if not cmd_file.exists():
                return {
                    "status": "error",
                    "command": cmd_name,
                    "error": f"Command not found: {cmd_name}",
                    "timestamp": self._get_timestamp()
                }

            # Read command definition
            with open(cmd_file, 'r') as f:
                cmd_content = f.read()

            # Execute command
            # NOTE: In actual implementation, this would invoke Cursor's
            # SlashCommand tool. For now, we provide a structure for agent use.
            result = self._execute_command(cmd_name, cmd_content, args)

            # Log execution
            execution_log = {
                "command": cmd_name,
                "args": args,
                "result": result,
                "timestamp": self._get_timestamp()
            }
            self.execution_history.append(execution_log)

            # Store in context if available
            if self.context is not None:
                if "commands_executed" not in self.context:
                    self.context["commands_executed"] = []
                self.context["commands_executed"].append({
                    cmd_name: {"args": args, "result": result}
                })

            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "command": cmd_name,
                "args": args,
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
            self.execution_history.append(error_result)
            return error_result

    def list_available(self) -> List[Dict[str, str]]:
        """
        List available slash commands

        Returns:
            List of command info dictionaries

        Example:
            commands = Commands()
            available = commands.list_available()
            # [{"name": "review-pr", "file": "/path/to/review-pr.md"}, ...]
        """
        command_files = list(self.commands_dir.glob("*.md"))

        commands = []
        for cmd_file in command_files:
            commands.append({
                "name": cmd_file.stem,
                "file": str(cmd_file),
                "description": self._get_command_description(cmd_file)
            })

        return commands

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get command execution history

        Returns:
            List of execution records
        """
        return self.execution_history

    def clear_history(self):
        """Clear command execution history"""
        self.execution_history.clear()

    def _execute_command(self, cmd_name: str, cmd_content: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to execute command

        NOTE: This is a placeholder for actual Cursor SlashCommand tool invocation.

        Args:
            cmd_name: Command name
            cmd_content: Command definition content
            args: Command arguments

        Returns:
            Command result
        """
        # Placeholder implementation
        # In actual implementation, this would use Cursor's SlashCommand tool

        return {
            "status": "success",
            "command": cmd_name,
            "args": args,
            "output": f"Command {cmd_name} executed successfully",
            "timestamp": self._get_timestamp()
        }

    def _get_command_description(self, cmd_file: Path) -> str:
        """
        Extract description from command file

        Args:
            cmd_file: Path to command file

        Returns:
            Command description (first line after frontmatter)
        """
        try:
            with open(cmd_file, 'r') as f:
                content = f.read()

            # Skip frontmatter if present
            lines = content.split('\n')
            in_frontmatter = False
            description = ""

            for line in lines:
                if line.strip() == '---':
                    in_frontmatter = not in_frontmatter
                    continue

                if not in_frontmatter and line.strip():
                    # First non-empty line after frontmatter
                    description = line.strip('# ').strip()
                    break

            return description

        except Exception:
            return ""

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"


# Example usage
if __name__ == "__main__":
    # Create commands instance
    commands = Commands()

    # Execute a command
    result = commands.execute("/review-pr", pr_number=123)
    print(f"Command result: {json.dumps(result, indent=2)}")

    # List available commands
    available = commands.list_available()
    print(f"Available commands: {json.dumps(available, indent=2)}")

    # Get execution history
    history = commands.get_history()
    print(f"Execution history: {json.dumps(history, indent=2)}")
