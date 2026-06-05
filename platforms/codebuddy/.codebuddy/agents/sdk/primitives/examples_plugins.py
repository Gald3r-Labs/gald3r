"""
Examples: Plugins Integration

Demonstrates how to use the Plugins primitive in SDK agents.
"""

import json
from plugins import Plugins


def example_1_basic_search():
    """Example 1: Basic web search using Brave Search plugin"""
    print("\n=== Example 1: Basic Web Search ===\n")

    plugins = Plugins()

    # Search for API design patterns
    result = plugins.call(
        "mcp__brave_search",
        query="FastAPI authentication best practices",
        max_results=5
    )

    print(f"Status: {result['status']}")
    print(f"Plugin: {result['plugin']}")
    print(f"\nResults:")
    for item in result.get("data", {}).get("results", []):
        print(f"  - {item.get('title')}: {item.get('url')}")


def example_2_with_context():
    """Example 2: Plugin with agent context (auto-storage)"""
    print("\n=== Example 2: Plugin with Context ===\n")

    # Simulate agent context
    agent_context = {
        "task": "Build authentication API",
        "phase": "research"
    }

    plugins = Plugins(context=agent_context)

    # Call plugin - result automatically stored in context
    plugins.call(
        "mcp__brave_search",
        query="OAuth2 implementation examples"
    )

    # Context now contains plugin results
    print("Context after plugin call:")
    print(json.dumps(agent_context.get("plugin_results", {}), indent=2))


def example_3_github_integration():
    """Example 3: GitHub plugin for repository operations"""
    print("\n=== Example 3: GitHub Integration ===\n")

    plugins = Plugins()

    # Search GitHub for authentication libraries
    result = plugins.call(
        "mcp__github",
        action="search_repositories",
        query="authentication library python",
        sort="stars",
        limit=5
    )

    if result["status"] == "success":
        print("Top authentication libraries:")
        for repo in result.get("data", {}).get("repositories", []):
            print(f"  - {repo.get('name')} ({repo.get('stars')} stars)")


def example_4_database_query():
    """Example 4: PostgreSQL plugin for database queries"""
    print("\n=== Example 4: Database Query ===\n")

    plugins = Plugins()

    # Query database schema
    result = plugins.call(
        "mcp__postgres",
        action="execute_query",
        query="SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    )

    if result["status"] == "success":
        print("Database tables:")
        for row in result.get("data", {}).get("rows", []):
            print(f"  - {row['table_name']}")


def example_5_multiple_plugins():
    """Example 5: Chaining multiple plugins in workflow"""
    print("\n=== Example 5: Multiple Plugins Workflow ===\n")

    plugins = Plugins()

    # Step 1: Search for examples
    print("Step 1: Searching for examples...")
    search_result = plugins.call(
        "mcp__brave_search",
        query="FastAPI user authentication tutorial"
    )

    # Step 2: Fetch detailed content from top result
    if search_result["status"] == "success":
        top_url = search_result["data"]["results"][0]["url"]
        print(f"Step 2: Fetching content from {top_url}...")

        fetch_result = plugins.call(
            "mcp__fetch",
            url=top_url,
            format="markdown"
        )

        if fetch_result["status"] == "success":
            print("Content fetched successfully")
            print(f"Preview: {fetch_result['data']['content'][:200]}...")

    # Step 3: Review invocation log
    print("\nStep 3: Plugin invocation log:")
    log = plugins.get_invocation_log()
    for entry in log:
        print(f"  [{entry['timestamp']}] {entry['plugin']}: {entry.get('status', 'pending')}")


def example_6_error_handling():
    """Example 6: Handling plugin errors"""
    print("\n=== Example 6: Error Handling ===\n")

    plugins = Plugins()

    # Try to call non-existent plugin
    result = plugins.call("mcp__nonexistent", param="value")

    if result["status"] == "error":
        print(f"Error occurred: {result['error']}")
        print("Gracefully handling failure...")

    # Try with invalid parameters
    result = plugins.call("mcp__brave_search")  # Missing required 'query'

    if result["status"] == "error":
        print(f"Error: {result['error']}")


def example_7_caching():
    """Example 7: Plugin result caching"""
    print("\n=== Example 7: Result Caching ===\n")

    plugins = Plugins()

    # First call (hits plugin)
    print("First call (no cache)...")
    result1 = plugins.call("mcp__brave_search", query="Python testing")

    # Second call with same params (uses cache internally)
    print("Second call (cache available)...")
    result2 = plugins.call("mcp__brave_search", query="Python testing")

    print(f"Results match: {result1['timestamp'] == result2['timestamp']}")

    # Clear cache
    plugins.clear_cache()
    print("Cache cleared")


def example_8_list_available():
    """Example 8: Discovering available plugins"""
    print("\n=== Example 8: List Available Plugins ===\n")

    plugins = Plugins()

    available = plugins.list_available()
    print(f"Found {len(available)} available plugins:")
    for plugin in available:
        print(f"  - {plugin}")


def example_9_agent_workflow():
    """Example 9: Complete agent workflow with plugins"""
    print("\n=== Example 9: Agent Workflow ===\n")

    class BackendDeveloperAgent:
        def __init__(self):
            self.plugins = Plugins()

        def research_authentication(self, context):
            """Research authentication patterns using plugins"""

            # Search for best practices
            search_result = self.plugins.call(
                "mcp__brave_search",
                query="FastAPI JWT authentication best practices"
            )

            # Check GitHub for popular libraries
            github_result = self.plugins.call(
                "mcp__github",
                action="search_repositories",
                query="FastAPI authentication",
                sort="stars"
            )

            # Update context with findings
            context["research"] = {
                "web_results": search_result["data"],
                "github_libraries": github_result["data"],
                "recommendation": "Use FastAPI-Users with JWT tokens"
            }

            return context

    # Use agent
    agent = BackendDeveloperAgent()
    context = {"task": "Implement authentication"}

    updated_context = agent.research_authentication(context)
    print("Research complete:")
    print(json.dumps(updated_context.get("research", {}), indent=2))


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CLAUDE CODE PRIMITIVES - PLUGINS EXAMPLES")
    print("="*60)

    # Run examples
    example_1_basic_search()
    example_2_with_context()
    example_3_github_integration()
    example_4_database_query()
    example_5_multiple_plugins()
    example_6_error_handling()
    example_7_caching()
    example_8_list_available()
    example_9_agent_workflow()

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")
