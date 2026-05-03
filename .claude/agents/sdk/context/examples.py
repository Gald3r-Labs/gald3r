"""
Context System Examples

Demonstrates common usage patterns for the hybrid context system.

Author: Database Expert Agent
Date: 2025-11-01
Task: 052 - Anthropic Agent SDK Integration
"""

from datetime import datetime, timedelta
from pathlib import Path

from .manager import ContextManager
from .schema import AgentContext, AgentMode, WorkflowMetadata
from .utils import (
    analyze_context_performance,
    export_context_report,
    validate_context,
)


def example_1_simple_workflow():
    """Example 1: Simple single-agent workflow"""
    print("\n=== Example 1: Simple Workflow ===\n")

    manager = ContextManager()

    # Create context
    context = manager.create_context(
        task="Add user profile page",
        project_path="/mnt/c/git/myproject",
        priority="medium",
        workflow_type="feature",
        tags=["frontend", "user-profile"]
    )

    print(f"Created workflow: {context.workflow_id}")

    # Simulate agent work
    context.mark_agent_started("frontend-developer", AgentMode.SDK)

    state = context.get_agent_state("frontend-developer")
    state.files_created = ["src/components/UserProfile.tsx", "src/pages/ProfilePage.tsx"]
    state.files_modified = ["src/routes.tsx"]
    state.tests_passing = True

    context.mark_agent_completed("frontend-developer")
    context.mark_completed()

    # Save
    manager.save_context(context)

    print(f"✅ Workflow completed")
    print(f"   Files created: {len(state.files_created)}")
    print(f"   Duration: {(context.completed_at - context.started_at).total_seconds():.1f}s")


def example_2_multi_agent_sequential():
    """Example 2: Multi-agent sequential workflow"""
    print("\n=== Example 2: Sequential Multi-Agent Workflow ===\n")

    manager = ContextManager()

    # Create context
    context = manager.create_context(
        task="Implement user authentication system",
        project_path="/mnt/c/git/myproject",
        priority="high",
        workflow_type="fullstack_feature",
        tags=["auth", "security", "backend", "frontend"]
    )

    print(f"Created workflow: {context.workflow_id}")

    # Agent 1: Database Expert
    print("\n[1/3] Database Expert...")
    context.mark_agent_started("database-expert", AgentMode.SDK)

    state = context.get_agent_state("database-expert")
    state.files_created = [
        "migrations/001_create_users.sql",
        "migrations/002_create_sessions.sql"
    ]

    context.shared_artifacts.database_schema = {
        "tables": ["users", "sessions", "tokens"],
        "migrations": ["001_create_users.sql", "002_create_sessions.sql"]
    }

    context.mark_agent_completed("database-expert")
    manager.save_context(context)
    print("   ✅ Database schema created")

    # Agent 2: Backend Developer
    print("\n[2/3] Backend Developer...")
    context.mark_agent_started("backend-developer", AgentMode.SDK)

    state = context.get_agent_state("backend-developer")
    state.files_created = [
        "src/auth/login.ts",
        "src/auth/logout.ts",
        "src/auth/register.ts"
    ]
    state.plugins_called = ["mcp__brave_search"]
    state.memory_accessed = ["database_preference"]

    # Access shared database schema
    db_schema = context.shared_artifacts.database_schema
    print(f"   Using database schema: {db_schema['tables']}")

    context.shared_artifacts.api_endpoints = [
        {"path": "/api/auth/login", "method": "POST", "file": "src/auth/login.ts"},
        {"path": "/api/auth/logout", "method": "POST", "file": "src/auth/logout.ts"},
        {"path": "/api/auth/register", "method": "POST", "file": "src/auth/register.ts"}
    ]

    context.mark_agent_completed("backend-developer")
    manager.save_context(context)
    print("   ✅ Backend API implemented")

    # Agent 3: Frontend Developer
    print("\n[3/3] Frontend Developer...")
    context.mark_agent_started("frontend-developer", AgentMode.SDK)

    state = context.get_agent_state("frontend-developer")
    state.files_created = [
        "src/components/LoginForm.tsx",
        "src/components/RegisterForm.tsx",
        "src/pages/AuthPage.tsx"
    ]

    # Access shared API endpoints
    api_endpoints = context.shared_artifacts.api_endpoints
    print(f"   Using API endpoints: {len(api_endpoints)} endpoints")

    context.mark_agent_completed("frontend-developer")
    context.mark_completed()

    manager.save_context(context)
    print("\n✅ Full-stack authentication complete")
    print(f"   Total agents: {len(context.agents_completed)}")
    print(f"   Total files: {sum(len(s.files_created) for s in context.agent_states.values())}")


def example_3_prompt_based_integration():
    """Example 3: Prompt-based agent integration"""
    print("\n=== Example 3: Prompt-Based Agent Integration ===\n")

    from ..prompt_based.context_adapter import ContextAdapter

    manager = ContextManager()
    adapter = ContextAdapter()

    # Create context
    context = manager.create_context(
        task="Add search functionality",
        project_path="/mnt/c/git/myproject",
        priority="medium"
    )

    print(f"Created workflow: {context.workflow_id}")

    # SDK agent runs first
    print("\n[1/2] Backend Developer (SDK)...")
    context.mark_agent_started("backend-developer", AgentMode.SDK)

    state = context.get_agent_state("backend-developer")
    state.files_created = ["src/api/search.ts"]

    context.shared_artifacts.api_endpoints = [
        {"path": "/api/search", "method": "GET", "file": "src/api/search.ts"}
    ]

    context.mark_agent_completed("backend-developer")
    manager.save_context(context)
    print("   ✅ Backend complete")

    # Convert to JSON for prompt-based agent
    json_path = adapter.to_json(context)
    print(f"\n[2/2] Frontend Developer (Prompt-based)...")
    print(f"   Context file: {json_path}")

    # Simulate prompt-based agent output
    agent_output = """
    # Frontend Implementation Complete

    ✅ Successfully implemented search UI

    **Files Created:**
    - src/components/SearchBar.tsx
    - src/components/SearchResults.tsx
    - src/pages/SearchPage.tsx

    **Files Modified:**
    - src/routes.tsx
    - src/App.tsx

    **Tests:** 12 tests passed

    ```json
    {
        "status": "completed",
        "tests_passing": true
    }
    ```
    """

    # Parse output
    result = adapter.from_text(agent_output)
    print(f"   Parsed status: {result['status']}")
    print(f"   Files created: {len(result['files_created'])}")

    # Update context
    adapter.update_context(
        str(context.workflow_id),
        "frontend-developer",
        {
            "status": "completed",
            "files_created": result["files_created"],
            "files_modified": result["files_modified"],
            "tests_passing": result["tests_passing"]
        }
    )

    print("   ✅ Frontend complete")
    print("\n✅ Hybrid workflow complete (SDK + Prompt-based)")


def example_4_fallback_tracking():
    """Example 4: Fallback mechanism tracking"""
    print("\n=== Example 4: Fallback Tracking ===\n")

    manager = ContextManager()

    context = manager.create_context(
        task="Deploy application to production",
        project_path="/mnt/c/git/myproject",
        priority="high"
    )

    print(f"Created workflow: {context.workflow_id}")

    # Try SDK agent, fails
    print("\n[Attempt 1] DevOps Engineer (SDK)...")
    context.mark_agent_started("devops-engineer", AgentMode.SDK)

    # Simulate SDK failure
    context.add_fallback(
        agent="devops-engineer",
        reason="SDK timeout after 120s",
        fallback_to="prompt-based",
        success=False
    )
    print("   ❌ SDK agent failed")
    print("   🔄 Falling back to prompt-based...")

    # Retry with prompt-based
    print("\n[Attempt 2] DevOps Engineer (Prompt-based)...")
    context.mark_agent_started("devops-engineer", AgentMode.PROMPT_BASED)

    state = context.get_agent_state("devops-engineer")
    state.retry_count = 1
    state.files_created = [".github/workflows/deploy.yml"]

    context.add_fallback(
        agent="devops-engineer",
        reason="Retried with prompt-based",
        fallback_to="prompt-based",
        success=True
    )

    context.mark_agent_completed("devops-engineer")
    manager.save_context(context)

    print("   ✅ Prompt-based agent succeeded")
    print(f"\n✅ Workflow complete with fallback")
    print(f"   Fallback events: {len(context.fallback_log)}")


def example_5_performance_analysis():
    """Example 5: Performance analysis and reporting"""
    print("\n=== Example 5: Performance Analysis ===\n")

    manager = ContextManager()

    # Create and complete workflow
    context = manager.create_context(
        task="Refactor authentication module",
        project_path="/mnt/c/git/myproject",
        priority="medium"
    )

    # Simulate multiple agents
    for agent_name in ["backend-developer", "test-runner", "code-reviewer"]:
        context.mark_agent_started(agent_name, AgentMode.SDK)

        state = context.get_agent_state(agent_name)
        state.files_created = ["test1.py", "test2.py"]
        state.files_modified = ["test3.py"]
        state.plugins_called = ["mcp__brave_search"]
        state.tests_passing = True

        context.mark_agent_completed(agent_name)

    context.mark_completed()
    manager.save_context(context)

    # Analyze performance
    print("Analyzing workflow performance...\n")
    metrics = analyze_context_performance(context)

    print("Performance Metrics:")
    print(f"  Efficiency Score: {metrics['efficiency_score']:.1f}/100")
    print(f"  Agents Executed: {metrics['agents_executed']}")
    print(f"  Agents Completed: {metrics['agents_completed']}")
    print(f"  Total Files Created: {metrics['total_files_created']}")
    print(f"  Total Files Modified: {metrics['total_files_modified']}")
    print(f"  Plugins Used: {', '.join(metrics['plugins_used'])}")
    print(f"  Fallback Count: {metrics['fallback_count']}")

    # Export report
    report_dir = Path(".claude/agent_context/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{context.workflow_id}.md"

    export_context_report(context, str(report_path))
    print(f"\n✅ Report exported to: {report_path}")


def example_6_context_search():
    """Example 6: Context search and filtering"""
    print("\n=== Example 6: Context Search ===\n")

    manager = ContextManager()

    # Create multiple contexts
    for i in range(5):
        context = manager.create_context(
            task=f"Test workflow {i+1}",
            project_path="/mnt/c/git/myproject",
            priority=["low", "medium", "high"][i % 3],
            workflow_type=["feature", "bugfix", "refactor"][i % 3],
            tags=[["frontend"], ["backend"], ["fullstack"]][i % 3]
        )

        # Mark some as completed
        if i < 3:
            context.mark_agent_started("backend-developer")
            context.mark_agent_completed("backend-developer")
            context.mark_completed()
            manager.save_context(context)
            manager.archive_context(str(context.workflow_id))

    # Search examples
    print("\n1. Search by priority:")
    results = manager.search_contexts(priority="high", limit=5)
    print(f"   Found {len(results)} high-priority workflows")

    print("\n2. Search by task keyword:")
    results = manager.search_contexts(task_query="workflow", limit=5)
    print(f"   Found {len(results)} workflows matching 'workflow'")

    print("\n3. Search by status:")
    results = manager.search_contexts(status="completed", limit=5)
    print(f"   Found {len(results)} completed workflows")

    print("\n4. List active workflows:")
    active = manager.list_active_contexts()
    print(f"   Found {len(active)} active workflows")

    print("\n5. List archived workflows:")
    archived = manager.list_archived_contexts(limit=10)
    print(f"   Found {len(archived)} archived workflows")

    print("\n✅ Search examples complete")


def example_7_cleanup_and_maintenance():
    """Example 7: Context cleanup and maintenance"""
    print("\n=== Example 7: Cleanup and Maintenance ===\n")

    manager = ContextManager()

    # Get storage stats
    print("1. Storage Statistics:")
    stats = manager.get_context_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Dry run cleanup
    print("\n2. Cleanup (Dry Run):")
    expired = manager.cleanup_expired(dry_run=True)
    print(f"   Would archive {len(expired)} expired contexts")

    # Validation
    print("\n3. Validate Active Contexts:")
    active = manager.list_active_contexts()
    for context in active:
        issues = validate_context(context)
        if issues:
            print(f"   ⚠️ {context.workflow_id}:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print(f"   ✅ {context.workflow_id}: No issues")

    print("\n✅ Maintenance complete")


def run_all_examples():
    """Run all examples"""
    print("=" * 60)
    print("Context System Examples")
    print("=" * 60)

    try:
        example_1_simple_workflow()
        example_2_multi_agent_sequential()
        example_3_prompt_based_integration()
        example_4_fallback_tracking()
        example_5_performance_analysis()
        example_6_context_search()
        example_7_cleanup_and_maintenance()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()
