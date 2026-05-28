"""
Example 2: Sequential Multi-Agent Workflow

Demonstrates:
- Creating multiple agents
- Running agents sequentially
- Context passing between agents
- Workflow orchestration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from context import AgentContext
from workflow import AgentWorkflow


class DatabaseExpert(BaseAgent):
    """Database design agent"""

    def __init__(self):
        super().__init__(
            name="database-expert",
            description="Database schema and migrations",
            tools=["Read", "Write"]
        )

    def process(self, context: AgentContext):
        task = context.get("task")
        self.logger.info(f"Designing database for: {task}")

        # Create database schema
        schema = {
            "tables": ["users", "sessions", "roles"],
            "migrations": [
                "001_create_users.sql",
                "002_create_sessions.sql",
                "003_create_roles.sql"
            ]
        }

        # Update context
        context.set("database_schema", schema)
        context.set("database_complete", True)

        return {
            "status": "completed",
            "tables_created": len(schema["tables"]),
            "migrations": len(schema["migrations"])
        }


class BackendDeveloper(BaseAgent):
    """Backend API development agent"""

    def __init__(self):
        super().__init__(
            name="backend-developer",
            description="Backend API implementation",
            tools=["Read", "Write", "Edit", "Bash"]
        )

    def process(self, context: AgentContext):
        # Check for database schema
        schema = context.get("database_schema")
        if not schema:
            return {
                "status": "failed",
                "error": "Database schema not found. Run database-expert first."
            }

        self.logger.info(f"Building API with {len(schema['tables'])} tables")

        # Create API endpoints
        endpoints = [
            "/api/auth/login",
            "/api/auth/logout",
            "/api/users",
            "/api/sessions"
        ]

        # Update context
        context.set("api_endpoints", endpoints)
        context.set("backend_complete", True)

        return {
            "status": "completed",
            "endpoints_created": len(endpoints),
            "tests_passing": True
        }


class FrontendDeveloper(BaseAgent):
    """Frontend UI development agent"""

    def __init__(self):
        super().__init__(
            name="frontend-developer",
            description="Frontend UI components",
            tools=["Read", "Write", "Edit"]
        )

    def process(self, context: AgentContext):
        # Check for API endpoints
        endpoints = context.get("api_endpoints")
        if not endpoints:
            return {
                "status": "failed",
                "error": "API endpoints not found. Run backend-developer first."
            }

        self.logger.info(f"Building UI for {len(endpoints)} endpoints")

        # Create UI components
        components = [
            "LoginForm.tsx",
            "LogoutButton.tsx",
            "UserProfile.tsx",
            "SessionManager.tsx"
        ]

        # Update context
        context.set("ui_components", components)
        context.set("frontend_complete", True)

        return {
            "status": "completed",
            "components_created": len(components),
            "tests_passing": True
        }


def main():
    print("=" * 60)
    print("Example 2: Sequential Multi-Agent Workflow")
    print("=" * 60)

    # Create workflow
    workflow = AgentWorkflow(enable_progress_tracking=True)

    # Create context
    context = workflow.create_context(
        task="Build complete authentication system",
        priority="high"
    )

    print(f"\nWorkflow ID: {context.workflow_id}")
    print(f"Task: {context.task}")

    # Define agent sequence
    agents = [
        ("database-expert", DatabaseExpert()),
        ("backend-developer", BackendDeveloper()),
        ("frontend-developer", FrontendDeveloper())
    ]

    print(f"\nRunning {len(agents)} agents sequentially...")
    print("-" * 60)

    # Run workflow
    result = workflow.run_sequential(agents, context)

    # Display results
    print("\n" + "=" * 60)
    print("Workflow Result:")
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Agents Run: {', '.join(result['agents_run'])}")

    print("\n" + "-" * 60)
    print("Agent Results:")
    print("-" * 60)
    for agent_name, agent_result in result['results'].items():
        print(f"\n{agent_name}:")
        for key, value in agent_result.items():
            print(f"  {key}: {value}")

    print("\n" + "-" * 60)
    print("Final Context State:")
    print("-" * 60)
    print(f"Database Schema: {len(context.get('database_schema', {}).get('tables', []))} tables")
    print(f"API Endpoints: {len(context.get('api_endpoints', []))} endpoints")
    print(f"UI Components: {len(context.get('ui_components', []))} components")
    print(f"Agents Completed: {', '.join(context.agents_completed)}")

    # Archive workflow
    print(f"\nArchiving workflow...")
    workflow.archive_workflow(context.workflow_id)

    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()
