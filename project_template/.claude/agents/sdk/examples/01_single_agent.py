"""
Example 1: Running a Single Agent

Demonstrates:
- Creating a custom agent
- Creating a context
- Running a single agent
- Accessing results
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from context import AgentContext


class SimpleBackendAgent(BaseAgent):
    """Simple backend development agent for demonstration"""

    def __init__(self):
        super().__init__(
            name="backend-developer",
            description="Backend API development",
            model="claude-opus-4-5",
            tools=["Read", "Write", "Edit", "Bash"]
        )

    def process(self, context: AgentContext):
        """
        Implement a simple API endpoint

        Args:
            context: Shared context with task

        Returns:
            Agent result dictionary
        """
        # Get task from context
        task = context.get("task")
        self.logger.info(f"Processing task: {task}")

        # Simulate backend work
        endpoints = [
            "/api/auth/login",
            "/api/auth/logout",
            "/api/auth/refresh"
        ]

        # Update context with results
        context.set("backend_complete", True)
        context.set("api_endpoints", endpoints)
        context.set("tests_passing", True)

        return {
            "status": "completed",
            "endpoints_created": len(endpoints),
            "tests_passing": True
        }


def main():
    print("=" * 60)
    print("Example 1: Running a Single Agent")
    print("=" * 60)

    # Create context
    context = AgentContext(
        task="Build user authentication API",
        priority="high",
        user_id="demo-user"
    )

    print(f"\nWorkflow ID: {context.workflow_id}")
    print(f"Task: {context.task}")

    # Create and run agent
    print("\nRunning backend developer agent...")
    backend = SimpleBackendAgent()

    result = backend.run(context)

    # Display results
    print("\n" + "-" * 60)
    print("Agent Result:")
    print("-" * 60)
    print(f"Status: {result['status']}")
    print(f"Endpoints Created: {result['endpoints_created']}")
    print(f"Tests Passing: {result['tests_passing']}")

    print("\n" + "-" * 60)
    print("Context After Agent:")
    print("-" * 60)
    print(f"Backend Complete: {context.get('backend_complete')}")
    print(f"API Endpoints: {context.get('api_endpoints')}")
    print(f"Agents Completed: {context.agents_completed}")

    # Save context
    context_file = context.save()
    print(f"\nContext saved to: {context_file}")

    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()
