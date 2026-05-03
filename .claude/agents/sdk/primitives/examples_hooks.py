"""
Examples: Hooks Integration

Demonstrates how to use the Hooks primitive in SDK agents.
"""

import json
from hooks import Hooks


def example_1_basic_lifecycle():
    """Example 1: Basic lifecycle hooks"""
    print("\n=== Example 1: Basic Lifecycle Hooks ===\n")

    hooks = Hooks(agent_name="backend-developer")

    # Trigger start
    start_result = hooks.trigger("agent-start",
                                context={"task": "Build API"})
    print(f"Start hook: {start_result['status']}")

    # Simulate work...
    print("Working...")

    # Trigger completion
    complete_result = hooks.trigger("agent-complete",
                                   context={"task": "Build API"},
                                   result={"status": "success"})
    print(f"Complete hook: {complete_result['status']}")


def example_2_error_handling():
    """Example 2: Error hook for failures"""
    print("\n=== Example 2: Error Hook ===\n")

    hooks = Hooks(agent_name="backend-developer")

    try:
        # Simulate error
        raise Exception("Database connection failed")
    except Exception as e:
        # Trigger error hook
        error_result = hooks.trigger("agent-error",
                                    context={"task": "Build API"},
                                    error=str(e))
        print(f"Error hook triggered: {error_result['status']}")
        print(f"Error message: {e}")


def example_3_with_context_data():
    """Example 3: Passing rich context data to hooks"""
    print("\n=== Example 3: Rich Context Data ===\n")

    hooks = Hooks(agent_name="backend-developer")

    # Start with detailed context
    context = {
        "task": "Build authentication API",
        "requirements": {
            "auth_type": "JWT",
            "database": "PostgreSQL",
            "endpoints": ["/login", "/logout", "/refresh"]
        },
        "dependencies": ["FastAPI-Users", "python-jose"],
        "estimated_time": "4 hours"
    }

    result = hooks.trigger("agent-start", context=context)
    print(f"Hook triggered with rich context: {result['status']}")


def example_4_completion_with_results():
    """Example 4: Completion hook with results"""
    print("\n=== Example 4: Completion with Results ===\n")

    hooks = Hooks(agent_name="backend-developer")

    # Simulate completed work
    result = {
        "status": "success",
        "files_created": [
            "src/auth/jwt.py",
            "src/auth/users.py",
            "tests/test_auth.py"
        ],
        "endpoints_implemented": 3,
        "tests_passing": True,
        "test_coverage": 0.95,
        "performance_metrics": {
            "login_time": "150ms",
            "token_generation": "50ms"
        }
    }

    complete_result = hooks.trigger("agent-complete",
                                   context={"task": "Build auth API"},
                                   result=result)
    print(f"Completion hook with results: {complete_result['status']}")


def example_5_event_log():
    """Example 5: Hook event logging"""
    print("\n=== Example 5: Event Logging ===\n")

    hooks = Hooks(agent_name="backend-developer")

    # Trigger several events
    hooks.trigger("agent-start", context={"task": "Task 1"})
    hooks.trigger("agent-complete", context={"task": "Task 1"})
    hooks.trigger("agent-start", context={"task": "Task 2"})
    hooks.trigger("agent-complete", context={"task": "Task 2"})

    # Get event log
    event_log = hooks.get_event_log()

    print(f"Event log ({len(event_log)} events):")
    for event in event_log:
        print(f"  [{event['timestamp']}] {event['event']}: {event['agent']}")


def example_6_multiple_agents():
    """Example 6: Multiple agents with separate hooks"""
    print("\n=== Example 6: Multiple Agents ===\n")

    # Different agents have separate hook instances
    backend_hooks = Hooks(agent_name="backend-developer")
    frontend_hooks = Hooks(agent_name="frontend-developer")

    # Backend work
    backend_hooks.trigger("agent-start", context={"task": "Build API"})
    backend_hooks.trigger("agent-complete", context={"task": "Build API"})

    # Frontend work
    frontend_hooks.trigger("agent-start", context={"task": "Build UI"})
    frontend_hooks.trigger("agent-complete", context={"task": "Build UI"})

    # Each agent has separate event logs
    print(f"Backend events: {len(backend_hooks.get_event_log())}")
    print(f"Frontend events: {len(frontend_hooks.get_event_log())}")


def example_7_create_hook_templates():
    """Example 7: Creating hook script templates"""
    print("\n=== Example 7: Create Hook Templates ===\n")

    hooks = Hooks(agent_name="backend-developer")

    # Create templates for all events
    for event in Hooks.EVENTS:
        hooks.create_hook_template(event)
        print(f"Created template: {event}.sh")

    print(f"\nHook scripts created in: {hooks.hooks_dir}")


def example_8_custom_hook_script():
    """Example 8: Creating custom hook script"""
    print("\n=== Example 8: Custom Hook Script ===\n")

    hooks = Hooks(agent_name="backend-developer")

    # Custom completion hook
    custom_hook = """#!/bin/bash
# Custom agent-complete hook

EVENT_DATA=$(cat)
AGENT=$(echo "$EVENT_DATA" | jq -r '.agent')
TASK=$(echo "$EVENT_DATA" | jq -r '.data.context.task')
STATUS=$(echo "$EVENT_DATA" | jq -r '.data.result.status')

echo "[$(date)] $AGENT completed: $TASK ($STATUS)" >> .claude/logs/completions.log

# Send notification
if [ "$STATUS" = "success" ]; then
    echo "✓ Agent $AGENT completed successfully: $TASK"
else
    echo "✗ Agent $AGENT failed: $TASK"
fi

exit 0
"""

    hooks.create_hook_template("agent-complete", content=custom_hook)
    print("Custom completion hook created")


def example_9_validation_hook():
    """Example 9: Using hooks for validation"""
    print("\n=== Example 9: Validation Hook ===\n")

    hooks = Hooks(agent_name="backend-developer")

    # Validation hook ensures prerequisites
    validation_hook = """#!/bin/bash
# Validation hook - check prerequisites

EVENT_DATA=$(cat)

# Check if database is available
if ! pg_isready -h localhost > /dev/null 2>&1; then
    echo "ERROR: PostgreSQL not running"
    exit 1
fi

# Check if required env vars are set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

echo "✓ Prerequisites validated"
exit 0
"""

    hooks.create_hook_template("agent-start", content=validation_hook)
    print("Validation hook created")

    # When agent starts, hook will validate prerequisites
    result = hooks.trigger("agent-start", context={"task": "Build API"})
    print(f"Validation result: {result['status']}")


def example_10_agent_workflow():
    """Example 10: Complete agent workflow with hooks"""
    print("\n=== Example 10: Agent Workflow with Hooks ===\n")

    class BackendDeveloperAgent:
        def __init__(self):
            self.hooks = Hooks(agent_name="backend-developer")

        def process_task(self, context):
            """Process task with full lifecycle hooks"""

            # Trigger start hook (validation, logging)
            self.hooks.trigger("agent-start", context=context)

            try:
                # Do work
                print("  Processing task...")
                result = self._implement_feature(context)

                # Trigger completion hook (logging, notifications)
                self.hooks.trigger("agent-complete",
                                 context=context,
                                 result=result)

                return result

            except Exception as e:
                # Trigger error hook (error logging, alerting)
                self.hooks.trigger("agent-error",
                                 context=context,
                                 error=str(e))
                raise

        def _implement_feature(self, context):
            """Actual implementation"""
            return {
                "status": "success",
                "files_created": 5,
                "tests_passing": True
            }

    # Use agent
    agent = BackendDeveloperAgent()
    context = {"task": "Build authentication API"}

    result = agent.process_task(context)
    print(f"\nTask completed: {result['status']}")

    # Show event log
    event_log = agent.hooks.get_event_log()
    print(f"\nEvent log ({len(event_log)} events):")
    for event in event_log:
        print(f"  - {event['event']}")


def example_11_notification_hook():
    """Example 11: Notification hook for Slack/email"""
    print("\n=== Example 11: Notification Hook ===\n")

    hooks = Hooks(agent_name="backend-developer")

    # Notification hook for completions
    notification_hook = """#!/bin/bash
# Send notification on agent completion

EVENT_DATA=$(cat)
AGENT=$(echo "$EVENT_DATA" | jq -r '.agent')
TASK=$(echo "$EVENT_DATA" | jq -r '.data.context.task')
STATUS=$(echo "$EVENT_DATA" | jq -r '.data.result.status')

# Send to Slack
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    MESSAGE="Agent $AGENT completed: $TASK ($STATUS)"
    curl -X POST -H 'Content-type: application/json' \
         --data "{\\"text\\":\\"$MESSAGE\\"}" \
         "$SLACK_WEBHOOK_URL"
fi

# Send email (optional)
if [ "$STATUS" = "error" ] && [ -n "$ADMIN_EMAIL" ]; then
    echo "$TASK failed - check logs" | mail -s "Agent Error" "$ADMIN_EMAIL"
fi

exit 0
"""

    hooks.create_hook_template("agent-complete", content=notification_hook)
    print("Notification hook created")


def example_12_metrics_collection():
    """Example 12: Metrics collection via hooks"""
    print("\n=== Example 12: Metrics Collection ===\n")

    hooks = Hooks(agent_name="backend-developer")

    # Metrics hook
    metrics_hook = """#!/bin/bash
# Collect agent performance metrics

EVENT_DATA=$(cat)
AGENT=$(echo "$EVENT_DATA" | jq -r '.agent')
EVENT=$(echo "$EVENT_DATA" | jq -r '.event')
TIMESTAMP=$(echo "$EVENT_DATA" | jq -r '.timestamp')

# Write to metrics file
METRICS_FILE=".claude/metrics/agent_metrics.jsonl"
mkdir -p .claude/metrics
echo "$EVENT_DATA" >> "$METRICS_FILE"

# Aggregate metrics (example)
if [ "$EVENT" = "agent-complete" ]; then
    FILES_CREATED=$(echo "$EVENT_DATA" | jq -r '.data.result.files_created // 0')
    echo "$(date),agent_files_created,$FILES_CREATED" >> .claude/metrics/timeseries.csv
fi

exit 0
"""

    hooks.create_hook_template("agent-complete", content=metrics_hook)
    print("Metrics collection hook created")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CLAUDE CODE PRIMITIVES - HOOKS EXAMPLES")
    print("="*60)

    # Run examples
    example_1_basic_lifecycle()
    example_2_error_handling()
    example_3_with_context_data()
    example_4_completion_with_results()
    example_5_event_log()
    example_6_multiple_agents()
    example_7_create_hook_templates()
    example_8_custom_hook_script()
    example_9_validation_hook()
    example_10_agent_workflow()
    example_11_notification_hook()
    example_12_metrics_collection()

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")
