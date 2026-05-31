"""
Examples: Memory Integration

Demonstrates how to use the Memory primitive in SDK agents.
"""

import json
from memory import Memory


def example_1_basic_storage():
    """Example 1: Basic memory storage and recall"""
    print("\n=== Example 1: Basic Storage & Recall ===\n")

    memory = Memory(agent_name="backend-developer")

    # Store preferences
    memory.store("database_preference", "PostgreSQL")
    memory.store("test_framework", "pytest")
    memory.store("code_style", "black")

    # Recall preferences
    db = memory.recall("database_preference")
    tests = memory.recall("test_framework")
    style = memory.recall("code_style")

    print(f"Database: {db}")
    print(f"Test framework: {tests}")
    print(f"Code style: {style}")


def example_2_with_metadata():
    """Example 2: Storing with metadata"""
    print("\n=== Example 2: Storage with Metadata ===\n")

    memory = Memory(agent_name="backend-developer")

    # Store with metadata
    memory.store(
        "database_preference",
        "PostgreSQL",
        metadata={
            "source": "user_request",
            "confidence": 0.95,
            "task": "authentication_system",
            "reasoning": "User explicitly requested PostgreSQL for auth"
        }
    )

    # Retrieve and show metadata
    all_memories = memory.list_all()
    db_memory = all_memories["database_preference"]

    print("Memory entry:")
    print(json.dumps(db_memory, indent=2))


def example_3_default_values():
    """Example 3: Using default values"""
    print("\n=== Example 3: Default Values ===\n")

    memory = Memory(agent_name="backend-developer")

    # Recall with default (key doesn't exist)
    api_framework = memory.recall("api_framework", default="FastAPI")
    cache_system = memory.recall("cache_system", default="Redis")

    print(f"API Framework: {api_framework} (default)")
    print(f"Cache System: {cache_system} (default)")

    # Store for future use
    memory.store("api_framework", "FastAPI")
    memory.store("cache_system", "Redis")

    # Next recall won't need default
    api_framework = memory.recall("api_framework")
    print(f"API Framework: {api_framework} (stored)")


def example_4_search():
    """Example 4: Searching memories"""
    print("\n=== Example 4: Search Memories ===\n")

    memory = Memory(agent_name="backend-developer")

    # Store various authentication-related memories
    memory.store("auth_library", "FastAPI-Users")
    memory.store("auth_token_type", "JWT")
    memory.store("auth_refresh_enabled", True)
    memory.store("database_auth_table", "users")

    # Search for authentication-related memories
    auth_memories = memory.search("auth")

    print(f"Found {len(auth_memories)} authentication-related memories:")
    for mem in auth_memories:
        print(f"  - {mem['key']}: {mem['value']}")


def example_5_persistence():
    """Example 5: Memory persistence across sessions"""
    print("\n=== Example 5: Persistence Across Sessions ===\n")

    # Session 1: Store preferences
    print("Session 1: Storing preferences...")
    memory1 = Memory(agent_name="backend-developer")
    memory1.store("database_preference", "PostgreSQL")
    memory1.store("preferred_orm", "SQLAlchemy")

    # Session 2: Load preferences (simulated)
    print("Session 2: Loading preferences...")
    memory2 = Memory(agent_name="backend-developer")  # Loads from disk
    db = memory2.recall("database_preference")
    orm = memory2.recall("preferred_orm")

    print(f"Loaded database: {db}")
    print(f"Loaded ORM: {orm}")
    print("✓ Persistence verified!")


def example_6_learning_patterns():
    """Example 6: Learning from successful patterns"""
    print("\n=== Example 6: Learning Successful Patterns ===\n")

    memory = Memory(agent_name="backend-developer")

    # Store successful implementation pattern
    success_pattern = {
        "task": "user_authentication",
        "approach": "JWT with refresh tokens",
        "libraries": ["FastAPI-Users", "python-jose"],
        "files_created": [
            "src/auth/jwt.py",
            "src/auth/users.py",
            "src/models/user.py"
        ],
        "test_coverage": 0.95,
        "performance": "excellent"
    }

    memory.store(
        "last_successful_auth_implementation",
        success_pattern,
        metadata={
            "outcome": "success",
            "tests_passed": True,
            "user_satisfaction": "high"
        }
    )

    # Later, recall pattern for similar task
    pattern = memory.recall("last_successful_auth_implementation")
    if pattern:
        print("Found successful pattern for reference:")
        print(f"  Task: {pattern['task']}")
        print(f"  Approach: {pattern['approach']}")
        print(f"  Libraries: {', '.join(pattern['libraries'])}")
        print(f"  Test Coverage: {pattern['test_coverage']*100}%")


def example_7_statistics():
    """Example 7: Memory statistics"""
    print("\n=== Example 7: Memory Statistics ===\n")

    memory = Memory(agent_name="backend-developer")

    # Store some memories
    memory.store("pref1", "value1")
    memory.store("pref2", "value2")
    memory.store("pref3", "value3")

    # Get statistics
    stats = memory.get_stats()

    print("Memory Statistics:")
    print(json.dumps(stats, indent=2))


def example_8_cleanup():
    """Example 8: Memory cleanup"""
    print("\n=== Example 8: Memory Cleanup ===\n")

    memory = Memory(agent_name="backend-developer")

    # Store temporary preference
    memory.store("temporary_setting", "temp_value")
    print("Stored temporary setting")

    # Delete when no longer needed
    deleted = memory.delete("temporary_setting")
    print(f"Deleted: {deleted}")

    # Verify deletion
    value = memory.recall("temporary_setting", default="NOT_FOUND")
    print(f"Recall after delete: {value}")


def example_9_namespace_separation():
    """Example 9: Agent namespace separation"""
    print("\n=== Example 9: Agent Namespace Separation ===\n")

    # Different agents have separate memory spaces
    backend_memory = Memory(agent_name="backend-developer")
    frontend_memory = Memory(agent_name="frontend-developer")

    # Backend preferences
    backend_memory.store("framework", "FastAPI")
    backend_memory.store("database", "PostgreSQL")

    # Frontend preferences
    frontend_memory.store("framework", "React")
    frontend_memory.store("state_management", "Redux")

    # Each agent has isolated memories
    print(f"Backend framework: {backend_memory.recall('framework')}")
    print(f"Frontend framework: {frontend_memory.recall('framework')}")
    print(f"Backend database: {backend_memory.recall('database')}")
    print(f"Frontend state: {frontend_memory.recall('state_management')}")


def example_10_agent_workflow():
    """Example 10: Complete agent workflow with memory"""
    print("\n=== Example 10: Agent Workflow with Memory ===\n")

    class BackendDeveloperAgent:
        def __init__(self):
            self.memory = Memory(agent_name="backend-developer")

        def process_task(self, context):
            """Process task using stored preferences"""

            # Check for user preferences
            db = self.memory.recall("database_preference", default="PostgreSQL")
            orm = self.memory.recall("orm_preference", default="SQLAlchemy")
            test_framework = self.memory.recall("test_framework", default="pytest")

            print(f"Using preferences:")
            print(f"  Database: {db}")
            print(f"  ORM: {orm}")
            print(f"  Tests: {test_framework}")

            # Simulate successful implementation
            result = {
                "status": "success",
                "database": db,
                "orm": orm,
                "tests_passed": True
            }

            # Learn from success
            if result["tests_passed"]:
                self.memory.store("last_successful_setup", {
                    "database": db,
                    "orm": orm,
                    "test_framework": test_framework,
                    "task": context.get("task")
                })

            return result

    # Use agent
    agent = BackendDeveloperAgent()

    # First task - uses defaults
    context1 = {"task": "Build user API"}
    result1 = agent.process_task(context1)
    print(f"\nTask 1 result: {result1['status']}")

    # Store preference for next time
    agent.memory.store("database_preference", "PostgreSQL")

    # Second task - uses stored preference
    context2 = {"task": "Build products API"}
    result2 = agent.process_task(context2)
    print(f"\nTask 2 result: {result2['status']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CLAUDE CODE PRIMITIVES - MEMORY EXAMPLES")
    print("="*60)

    # Run examples
    example_1_basic_storage()
    example_2_with_metadata()
    example_3_default_values()
    example_4_search()
    example_5_persistence()
    example_6_learning_patterns()
    example_7_statistics()
    example_8_cleanup()
    example_9_namespace_separation()
    example_10_agent_workflow()

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")
