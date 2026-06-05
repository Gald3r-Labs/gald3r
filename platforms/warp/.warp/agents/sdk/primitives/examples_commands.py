"""
Examples: Commands Integration

Demonstrates how to use the Commands primitive in SDK agents.
"""

import json
from commands import Commands


def example_1_basic_execution():
    """Example 1: Basic command execution"""
    print("\n=== Example 1: Basic Command Execution ===\n")

    commands = Commands()

    # Execute review command
    result = commands.execute("/review")

    print(f"Command: {result['command']}")
    print(f"Status: {result['status']}")
    print(f"Output: {result.get('output', 'N/A')}")


def example_2_with_arguments():
    """Example 2: Command with arguments"""
    print("\n=== Example 2: Command with Arguments ===\n")

    commands = Commands()

    # Review specific PR
    result = commands.execute("/review-pr", pr_number=123)

    print(f"Command: {result['command']}")
    print(f"Arguments: {result['args']}")
    print(f"Status: {result['status']}")


def example_3_multiple_commands():
    """Example 3: Executing multiple commands in sequence"""
    print("\n=== Example 3: Multiple Commands ===\n")

    commands = Commands()

    # Command sequence
    print("1. Running tests...")
    test_result = commands.execute("/run-tests", suite="backend")

    print("2. Getting status...")
    status_result = commands.execute("/status", format="json")

    print("3. Creating task...")
    task_result = commands.execute("/new-task",
                                   title="Fix failing tests",
                                   priority="high")

    print("\nCommand execution summary:")
    for result in [test_result, status_result, task_result]:
        print(f"  - {result['command']}: {result['status']}")


def example_4_list_available():
    """Example 4: Discovering available commands"""
    print("\n=== Example 4: List Available Commands ===\n")

    commands = Commands()

    available = commands.list_available()

    print(f"Found {len(available)} available commands:")
    for cmd in available:
        print(f"  - /{cmd['name']}: {cmd.get('description', 'No description')}")


def example_5_execution_history():
    """Example 5: Command execution history"""
    print("\n=== Example 5: Execution History ===\n")

    commands = Commands()

    # Execute several commands
    commands.execute("/status")
    commands.execute("/review")
    commands.execute("/new-task", title="Test task")

    # Get history
    history = commands.get_history()

    print("Command execution history:")
    for entry in history:
        print(f"  [{entry['timestamp']}] {entry['command']}: {entry['result']['status']}")


def example_6_with_context():
    """Example 6: Command with agent context (auto-logging)"""
    print("\n=== Example 6: Command with Context ===\n")

    # Simulate agent context
    agent_context = {
        "task": "Build authentication API",
        "phase": "testing"
    }

    commands = Commands(context=agent_context)

    # Execute command - automatically logged in context
    commands.execute("/run-tests", suite="auth")

    # Context now contains command execution log
    print("Context after command execution:")
    print(json.dumps(agent_context.get("commands_executed", []), indent=2))


def example_7_error_handling():
    """Example 7: Handling command errors"""
    print("\n=== Example 7: Error Handling ===\n")

    commands = Commands()

    # Try to execute non-existent command
    result = commands.execute("/nonexistent-command")

    if result["status"] == "error":
        print(f"Error occurred: {result['error']}")
        print("Gracefully handling failure...")

    # Try command with invalid arguments
    result = commands.execute("/review-pr")  # Missing required pr_number

    if result["status"] == "error":
        print(f"Error: {result['error']}")


def example_8_workflow_automation():
    """Example 8: Automated workflow using commands"""
    print("\n=== Example 8: Workflow Automation ===\n")

    commands = Commands()

    # Workflow: Develop → Test → Review → Deploy
    workflow_steps = [
        ("/status", {"format": "json"}),
        ("/run-tests", {"suite": "all"}),
        ("/review", {}),
        ("/update-task", {"task_id": "001", "status": "completed"})
    ]

    print("Executing workflow...")
    for cmd, args in workflow_steps:
        result = commands.execute(cmd, **args)
        print(f"  {cmd}: {result['status']}")

        if result["status"] == "error":
            print(f"  ✗ Workflow failed at {cmd}")
            break
    else:
        print("  ✓ Workflow completed successfully")


def example_9_conditional_execution():
    """Example 9: Conditional command execution"""
    print("\n=== Example 9: Conditional Execution ===\n")

    commands = Commands()

    # Run tests
    test_result = commands.execute("/run-tests", suite="backend")

    # Only review if tests pass
    if test_result["status"] == "success":
        print("Tests passed! Running review...")
        review_result = commands.execute("/review")

        # Only create PR if review passes
        if review_result["status"] == "success":
            print("Review passed! Creating PR...")
            pr_result = commands.execute("/create-pr",
                                        title="Backend implementation",
                                        description="Implements authentication API")
            print(f"PR created: {pr_result['status']}")
    else:
        print("Tests failed! Skipping review and PR creation.")


def example_10_agent_workflow():
    """Example 10: Complete agent workflow with commands"""
    print("\n=== Example 10: Agent Workflow with Commands ===\n")

    class BackendDeveloperAgent:
        def __init__(self):
            self.commands = Commands()

        def implement_and_validate(self, context):
            """Implement feature with automated validation"""

            task = context.get("task")
            print(f"Implementing: {task}")

            # Step 1: Check current status
            status = self.commands.execute("/status")
            print(f"  1. Status check: {status['status']}")

            # Step 2: Implement feature (simulated)
            print("  2. Implementing feature...")
            # ... actual implementation ...

            # Step 3: Run tests
            tests = self.commands.execute("/run-tests", suite="backend")
            print(f"  3. Tests: {tests['status']}")

            if tests["status"] != "success":
                return {"status": "failed", "reason": "tests_failed"}

            # Step 4: Run code review
            review = self.commands.execute("/review")
            print(f"  4. Review: {review['status']}")

            if review["status"] != "success":
                return {"status": "failed", "reason": "review_failed"}

            # Step 5: Update task
            update = self.commands.execute("/update-task",
                                          task_id=context.get("task_id"),
                                          status="completed")
            print(f"  5. Task update: {update['status']}")

            return {
                "status": "completed",
                "tests_passed": True,
                "review_passed": True
            }

    # Use agent
    agent = BackendDeveloperAgent()
    context = {
        "task": "Build user authentication API",
        "task_id": "042"
    }

    result = agent.implement_and_validate(context)
    print(f"\nFinal result: {json.dumps(result, indent=2)}")


def example_11_planning_workflow():
    """Example 11: Planning workflow using commands"""
    print("\n=== Example 11: Planning Workflow ===\n")

    commands = Commands()

    # Start planning phase
    print("Starting planning phase...")

    # 1. Create project plan
    plan_result = commands.execute("/start-planning",
                                   project="Authentication System",
                                   scope="Backend API with JWT")

    # 2. Add feature requirements
    feature_result = commands.execute("/add-feature",
                                     feature="User Registration",
                                     priority="high")

    # 3. Create tasks from plan
    task_result = commands.execute("/new-task",
                                   title="Implement user registration endpoint",
                                   priority="high",
                                   estimated_effort="2 days")

    # 4. Get final status
    status_result = commands.execute("/status", format="json")

    print("Planning workflow complete:")
    print(f"  Plan created: {plan_result['status']}")
    print(f"  Feature added: {feature_result['status']}")
    print(f"  Task created: {task_result['status']}")
    print(f"  Status updated: {status_result['status']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CLAUDE CODE PRIMITIVES - COMMANDS EXAMPLES")
    print("="*60)

    # Run examples
    example_1_basic_execution()
    example_2_with_arguments()
    example_3_multiple_commands()
    example_4_list_available()
    example_5_execution_history()
    example_6_with_context()
    example_7_error_handling()
    example_8_workflow_automation()
    example_9_conditional_execution()
    example_10_agent_workflow()
    example_11_planning_workflow()

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")
