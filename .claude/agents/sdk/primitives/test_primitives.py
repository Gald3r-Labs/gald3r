"""
Test Suite for Claude Code Primitives

Tests all four primitives: Plugins, Memory, Commands, Hooks
"""

import json
import os
import tempfile
from pathlib import Path

from plugins import Plugins
from memory import Memory
from commands import Commands
from hooks import Hooks


class TestPlugins:
    """Test suite for Plugins primitive"""

    def test_basic_call(self):
        """Test basic plugin invocation"""
        plugins = Plugins()
        result = plugins.call("mcp__brave_search", query="test")

        assert result["status"] == "success"
        assert result["plugin"] == "mcp__brave_search"
        assert "data" in result
        print("✓ test_basic_call passed")

    def test_with_context(self):
        """Test plugin with context storage"""
        context = {}
        plugins = Plugins(context=context)

        plugins.call("mcp__brave_search", query="test")

        assert "plugin_results" in context
        assert "mcp__brave_search" in context["plugin_results"]
        print("✓ test_with_context passed")

    def test_list_available(self):
        """Test listing available plugins"""
        plugins = Plugins()
        available = plugins.list_available()

        assert isinstance(available, list)
        assert len(available) > 0
        assert "mcp__brave_search" in available
        print("✓ test_list_available passed")

    def test_invocation_log(self):
        """Test plugin invocation logging"""
        plugins = Plugins()

        plugins.call("mcp__brave_search", query="test1")
        plugins.call("mcp__brave_search", query="test2")

        log = plugins.get_invocation_log()
        assert len(log) == 2
        print("✓ test_invocation_log passed")

    def test_cache(self):
        """Test plugin result caching"""
        plugins = Plugins()

        # First call
        result1 = plugins.call("mcp__brave_search", query="test")
        # Second call (should use cache)
        result2 = plugins.call("mcp__brave_search", query="test")

        assert result1["timestamp"] == result2["timestamp"]
        print("✓ test_cache passed")

    def test_error_handling(self):
        """Test plugin error handling"""
        plugins = Plugins()

        # Non-existent plugin
        result = plugins.call("mcp__nonexistent")
        assert result["status"] == "error"
        print("✓ test_error_handling passed")


class TestMemory:
    """Test suite for Memory primitive"""

    def test_store_and_recall(self):
        """Test basic store and recall"""
        memory = Memory(agent_name="test-agent")

        memory.store("test_key", "test_value")
        value = memory.recall("test_key")

        assert value == "test_value"
        print("✓ test_store_and_recall passed")

    def test_default_value(self):
        """Test recall with default value"""
        memory = Memory(agent_name="test-agent")

        value = memory.recall("nonexistent", default="default_value")
        assert value == "default_value"
        print("✓ test_default_value passed")

    def test_metadata(self):
        """Test storing with metadata"""
        memory = Memory(agent_name="test-agent")

        memory.store("key", "value",
                    metadata={"source": "test", "confidence": 0.9})

        all_memories = memory.list_all()
        assert "key" in all_memories
        assert all_memories["key"]["metadata"]["source"] == "test"
        print("✓ test_metadata passed")

    def test_search(self):
        """Test memory search"""
        memory = Memory(agent_name="test-agent")

        memory.store("auth_type", "JWT")
        memory.store("auth_library", "FastAPI-Users")
        memory.store("database", "PostgreSQL")

        results = memory.search("auth")
        assert len(results) == 2
        print("✓ test_search passed")

    def test_delete(self):
        """Test memory deletion"""
        memory = Memory(agent_name="test-agent")

        memory.store("temp_key", "temp_value")
        deleted = memory.delete("temp_key")
        assert deleted is True

        value = memory.recall("temp_key", default="NOT_FOUND")
        assert value == "NOT_FOUND"
        print("✓ test_delete passed")

    def test_persistence(self):
        """Test memory persistence to disk"""
        agent_name = "test-persistence-agent"

        # Store in first instance
        memory1 = Memory(agent_name=agent_name)
        memory1.store("persistent_key", "persistent_value")

        # Load in second instance
        memory2 = Memory(agent_name=agent_name)
        value = memory2.recall("persistent_key")

        assert value == "persistent_value"
        print("✓ test_persistence passed")

    def test_statistics(self):
        """Test memory statistics"""
        memory = Memory(agent_name="test-agent")

        memory.store("key1", "value1")
        memory.store("key2", "value2")

        stats = memory.get_stats()
        assert stats["total_memories"] >= 2
        assert stats["agent"] == "test-agent"
        print("✓ test_statistics passed")

    def test_namespace_separation(self):
        """Test agent namespace separation"""
        memory1 = Memory(agent_name="agent1")
        memory2 = Memory(agent_name="agent2")

        memory1.store("shared_key", "value1")
        memory2.store("shared_key", "value2")

        assert memory1.recall("shared_key") == "value1"
        assert memory2.recall("shared_key") == "value2"
        print("✓ test_namespace_separation passed")


class TestCommands:
    """Test suite for Commands primitive"""

    def test_execute(self):
        """Test basic command execution"""
        commands = Commands()
        result = commands.execute("/status")

        assert "status" in result
        assert "command" in result
        print("✓ test_execute passed")

    def test_execute_with_args(self):
        """Test command execution with arguments"""
        commands = Commands()
        result = commands.execute("/review-pr", pr_number=123)

        assert result["args"]["pr_number"] == 123
        print("✓ test_execute_with_args passed")

    def test_list_available(self):
        """Test listing available commands"""
        commands = Commands()
        available = commands.list_available()

        assert isinstance(available, list)
        assert len(available) > 0
        print("✓ test_list_available passed")

    def test_execution_history(self):
        """Test command execution history"""
        commands = Commands()

        commands.execute("/status")
        commands.execute("/review")

        history = commands.get_history()
        assert len(history) >= 2
        print("✓ test_execution_history passed")

    def test_with_context(self):
        """Test command with context storage"""
        context = {}
        commands = Commands(context=context)

        commands.execute("/status")

        assert "commands_executed" in context
        assert len(context["commands_executed"]) >= 1
        print("✓ test_with_context passed")

    def test_nonexistent_command(self):
        """Test non-existent command error handling"""
        commands = Commands()
        result = commands.execute("/nonexistent")

        assert result["status"] == "error"
        print("✓ test_nonexistent_command passed")


class TestHooks:
    """Test suite for Hooks primitive"""

    def test_trigger_start(self):
        """Test triggering start hook"""
        hooks = Hooks(agent_name="test-agent")
        result = hooks.trigger("agent-start", context={"task": "test"})

        assert result["status"] == "success"
        assert result["event"] == "agent-start"
        print("✓ test_trigger_start passed")

    def test_trigger_complete(self):
        """Test triggering complete hook"""
        hooks = Hooks(agent_name="test-agent")
        result = hooks.trigger("agent-complete",
                              context={"task": "test"},
                              result={"status": "success"})

        assert result["status"] == "success"
        print("✓ test_trigger_complete passed")

    def test_trigger_error(self):
        """Test triggering error hook"""
        hooks = Hooks(agent_name="test-agent")
        result = hooks.trigger("agent-error",
                              context={"task": "test"},
                              error="Test error")

        assert result["status"] == "success"
        print("✓ test_trigger_error passed")

    def test_event_log(self):
        """Test hook event logging"""
        hooks = Hooks(agent_name="test-agent")

        hooks.trigger("agent-start", context={"task": "test"})
        hooks.trigger("agent-complete", context={"task": "test"})

        log = hooks.get_event_log()
        assert len(log) >= 2
        print("✓ test_event_log passed")

    def test_invalid_event(self):
        """Test invalid event handling"""
        hooks = Hooks(agent_name="test-agent")
        result = hooks.trigger("invalid-event")

        assert result["status"] == "error"
        print("✓ test_invalid_event passed")

    def test_create_template(self):
        """Test creating hook templates"""
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks = Hooks(agent_name="test-agent", hooks_dir=tmpdir)
            hooks.create_hook_template("agent-start")

            hook_file = Path(tmpdir) / "agent-start.sh"
            assert hook_file.exists()
            assert os.access(hook_file, os.X_OK)  # Check executable
            print("✓ test_create_template passed")


class TestIntegration:
    """Integration tests combining multiple primitives"""

    def test_agent_workflow(self):
        """Test complete agent workflow using all primitives"""

        class TestAgent:
            def __init__(self):
                self.memory = Memory(agent_name="integration-test-agent")
                self.plugins = Plugins()
                self.commands = Commands()
                self.hooks = Hooks(agent_name="integration-test-agent")

            def process(self, context):
                # Start hook
                self.hooks.trigger("agent-start", context=context)

                # Check memory
                db_pref = self.memory.recall("database", default="PostgreSQL")
                context["database"] = db_pref

                # Call plugin
                search_result = self.plugins.call("mcp__brave_search",
                                                 query="test")
                context["search_results"] = search_result

                # Execute command
                cmd_result = self.commands.execute("/status")
                context["status"] = cmd_result

                # Complete hook
                self.hooks.trigger("agent-complete",
                                 context=context,
                                 result={"status": "success"})

                return context

        # Use agent
        agent = TestAgent()
        context = {"task": "Integration test"}
        result = agent.process(context)

        assert "database" in result
        assert "search_results" in result
        assert "status" in result
        print("✓ test_agent_workflow passed")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*60)
    print("CLAUDE CODE PRIMITIVES - TEST SUITE")
    print("="*60 + "\n")

    # Plugins tests
    print("Testing Plugins...")
    test_plugins = TestPlugins()
    test_plugins.test_basic_call()
    test_plugins.test_with_context()
    test_plugins.test_list_available()
    test_plugins.test_invocation_log()
    test_plugins.test_cache()
    test_plugins.test_error_handling()
    print("✓ All Plugins tests passed\n")

    # Memory tests
    print("Testing Memory...")
    test_memory = TestMemory()
    test_memory.test_store_and_recall()
    test_memory.test_default_value()
    test_memory.test_metadata()
    test_memory.test_search()
    test_memory.test_delete()
    test_memory.test_persistence()
    test_memory.test_statistics()
    test_memory.test_namespace_separation()
    print("✓ All Memory tests passed\n")

    # Commands tests
    print("Testing Commands...")
    test_commands = TestCommands()
    test_commands.test_execute()
    test_commands.test_execute_with_args()
    test_commands.test_list_available()
    test_commands.test_execution_history()
    test_commands.test_with_context()
    test_commands.test_nonexistent_command()
    print("✓ All Commands tests passed\n")

    # Hooks tests
    print("Testing Hooks...")
    test_hooks = TestHooks()
    test_hooks.test_trigger_start()
    test_hooks.test_trigger_complete()
    test_hooks.test_trigger_error()
    test_hooks.test_event_log()
    test_hooks.test_invalid_event()
    test_hooks.test_create_template()
    print("✓ All Hooks tests passed\n")

    # Integration tests
    print("Testing Integration...")
    test_integration = TestIntegration()
    test_integration.test_agent_workflow()
    print("✓ All Integration tests passed\n")

    print("="*60)
    print("ALL TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
