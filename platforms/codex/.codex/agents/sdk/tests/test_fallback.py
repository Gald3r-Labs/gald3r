"""
Test Suite for Fallback and Error Handling System

Tests all fallback scenarios and ensures system reliability.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fallback import (
    FallbackHandler,
    HybridAgentInvoker,
    FailureReason,
    AgentType
)
from health import (
    HealthMonitor,
    HealthStatus,
    SDKAvailabilityCheck,
    APIKeyCheck,
    AgentFilesCheck,
    ContextStorageCheck,
    ResourceCheck
)


class TestFailureDetection:
    """Test failure reason detection"""

    def test_sdk_not_installed(self):
        handler = FallbackHandler()
        exc = ImportError("No module named 'anthropic'")
        reason = handler.detect_failure(exc)
        assert reason == FailureReason.SDK_NOT_INSTALLED

    def test_api_key_missing(self):
        handler = FallbackHandler()
        exc = ValueError("api_key is required")
        reason = handler.detect_failure(exc)
        assert reason == FailureReason.API_KEY_MISSING

    def test_network_failure(self):
        handler = FallbackHandler()
        exc = ConnectionError("Network unreachable")
        reason = handler.detect_failure(exc)
        assert reason == FailureReason.NETWORK_FAILURE

    def test_agent_timeout(self):
        handler = FallbackHandler()
        exc = TimeoutError("Agent execution timed out")
        reason = handler.detect_failure(exc)
        assert reason == FailureReason.AGENT_TIMEOUT

    def test_agent_crash(self):
        handler = FallbackHandler()
        exc = RuntimeError("Agent crashed")
        reason = handler.detect_failure(exc)
        assert reason == FailureReason.AGENT_CRASH


class TestFallbackDecisions:
    """Test fallback decision logic"""

    def test_immediate_fallback_sdk_not_installed(self):
        handler = FallbackHandler()
        exc = ImportError("No module named 'anthropic'")
        should_fallback = handler.should_fallback("backend-developer", exc)
        assert should_fallback is True

    def test_immediate_fallback_api_key_missing(self):
        handler = FallbackHandler()
        exc = ValueError("api_key is required")
        should_fallback = handler.should_fallback("backend-developer", exc)
        assert should_fallback is True

    def test_retry_on_network_failure(self):
        handler = FallbackHandler(enable_retry=True, max_retries=2)
        exc = ConnectionError("Network timeout")

        # First attempt - should retry
        should_fallback = handler.should_fallback("backend-developer", exc, retry_count=0)
        assert should_fallback is False

        # Second attempt - should retry
        should_fallback = handler.should_fallback("backend-developer", exc, retry_count=1)
        assert should_fallback is False

        # Third attempt - should fallback
        should_fallback = handler.should_fallback("backend-developer", exc, retry_count=2)
        assert should_fallback is True

    def test_no_retry_when_disabled(self):
        handler = FallbackHandler(enable_retry=False)
        exc = ConnectionError("Network timeout")
        should_fallback = handler.should_fallback("backend-developer", exc, retry_count=0)
        assert should_fallback is True


class TestContextConversion:
    """Test context conversion to JSON"""

    def test_dict_context(self, tmp_path):
        handler = FallbackHandler(context_dir=tmp_path)
        context = {
            "workflow_id": "test-123",
            "task": "Build API",
            "data": {"key": "value"}
        }

        context_file = handler.convert_context_to_json(context, "test-123")

        assert context_file is not None
        assert context_file.exists()

        # Verify content
        with open(context_file, 'r') as f:
            saved = json.load(f)

        assert saved["workflow_id"] == "test-123"
        assert saved["task"] == "Build API"
        assert "_metadata" in saved

    def test_object_context(self, tmp_path):
        handler = FallbackHandler(context_dir=tmp_path)

        class TestContext:
            workflow_id = "test-456"
            task = "Build feature"

        context = TestContext()
        context_file = handler.convert_context_to_json(context, "test-456")

        assert context_file is not None
        assert context_file.exists()

    def test_non_serializable_context(self, tmp_path):
        handler = FallbackHandler(context_dir=tmp_path)

        class NonSerializable:
            def __str__(self):
                return "ComplexObject"

        context = {
            "workflow_id": "test-789",
            "complex": NonSerializable(),
            "normal": "data"
        }

        context_file = handler.convert_context_to_json(context, "test-789")

        # Should still create file with what it can serialize
        assert context_file is not None
        assert context_file.exists()


class TestStatistics:
    """Test statistics tracking"""

    def test_fallback_logging(self):
        handler = FallbackHandler()

        context = {"workflow_id": "test"}

        # Log multiple fallbacks
        handler.log_fallback("backend-developer", FailureReason.SDK_NOT_INSTALLED, context, success=True)
        handler.log_fallback("frontend-developer", FailureReason.NETWORK_FAILURE, context, success=True)
        handler.log_fallback("backend-developer", FailureReason.AGENT_TIMEOUT, context, success=True)

        stats = handler.get_statistics()

        assert stats["total_invocations"] == 3
        assert stats["prompt_based_fallbacks"] == 3
        assert stats["failure_reasons"]["sdk_not_installed"] == 1
        assert stats["failure_reasons"]["network_failure"] == 1
        assert stats["failure_reasons"]["agent_timeout"] == 1
        assert stats["agents_failed"]["backend-developer"] == 2
        assert stats["agents_failed"]["frontend-developer"] == 1

    def test_repeated_failure_alert(self):
        handler = FallbackHandler()

        # Log 3 failures for same agent
        for _ in range(3):
            handler.log_fallback("security-auditor", FailureReason.AGENT_CRASH, success=False)

        # Should trigger alert at threshold
        alert = handler.alert_on_repeated_failures("security-auditor", threshold=3)
        assert alert is True

        # Should not trigger for different agent
        alert = handler.alert_on_repeated_failures("backend-developer", threshold=3)
        assert alert is False


class TestHybridAgentInvoker:
    """Test hybrid agent invocation"""

    def test_auto_detect_agent_type(self):
        invoker = HybridAgentInvoker()

        # This will depend on actual file structure
        # For testing, just verify method exists and returns a type
        agent_type = invoker.auto_detect_agent_type("backend-developer")
        assert isinstance(agent_type, AgentType)


class TestHealthMonitor:
    """Test health monitoring system"""

    def test_sdk_availability_check(self):
        check = SDKAvailabilityCheck()
        status = check.check()

        # Will be CRITICAL if SDK not installed, HEALTHY if installed
        assert status in [HealthStatus.HEALTHY, HealthStatus.CRITICAL]
        assert check.details is not None

    def test_api_key_check(self):
        check = APIKeyCheck()
        status = check.check()

        # Will depend on environment
        assert status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]

    def test_agent_files_check(self, tmp_path):
        # Create test agent directory
        agent_dir = tmp_path / "agents"
        agent_dir.mkdir()

        # Create some test agents
        sdk_dir = agent_dir / "sdk" / "agents"
        sdk_dir.mkdir(parents=True)
        (sdk_dir / "test_agent.py").write_text("# Test agent")

        prompt_dir = agent_dir / "prompt-based"
        prompt_dir.mkdir()
        (prompt_dir / "test_agent.md").write_text("# Test agent")

        check = AgentFilesCheck(agent_dir=agent_dir)
        status = check.check()

        assert status in [HealthStatus.HEALTHY, HealthStatus.WARNING]
        assert check.details["agents_found"] >= 2

    def test_context_storage_check(self, tmp_path):
        check = ContextStorageCheck(context_dir=tmp_path / "context")
        status = check.check()

        # Should create directory and succeed
        assert status == HealthStatus.HEALTHY
        assert (tmp_path / "context").exists()

    def test_resource_check(self):
        check = ResourceCheck()
        status = check.check()

        # Should always return a status
        assert status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert "memory_percent" in check.details
        assert "disk_percent" in check.details

    def test_health_monitor_run_checks(self, tmp_path):
        monitor = HealthMonitor(log_dir=tmp_path)
        report = monitor.run_checks()

        assert "timestamp" in report
        assert "overall_status" in report
        assert "checks" in report
        assert "summary" in report
        assert len(report["checks"]) > 0

    def test_agent_validation(self):
        monitor = HealthMonitor()

        # Will depend on actual agent files
        # Just test that method works
        valid, message = monitor.validate_agent("backend-developer")
        assert isinstance(valid, bool)
        assert isinstance(message, str)


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_fallback_workflow(self, tmp_path):
        """Test complete workflow from failure to fallback"""

        handler = FallbackHandler(
            log_dir=tmp_path / "logs",
            context_dir=tmp_path / "context",
            enable_retry=True,
            max_retries=1
        )

        # Simulate SDK failure
        context = {
            "workflow_id": "integration-test",
            "task": "Build authentication system"
        }

        # Detect failure
        exc = ImportError("No module named 'anthropic'")
        reason = handler.detect_failure(exc)
        assert reason == FailureReason.SDK_NOT_INSTALLED

        # Should fallback immediately (no retry for this type)
        should_fallback = handler.should_fallback("backend-developer", exc)
        assert should_fallback is True

        # Convert context
        context_file = handler.convert_context_to_json(context)
        assert context_file is not None
        assert context_file.exists()

        # Call prompt agent (would invoke actual agent in production)
        result = handler.call_prompt_agent("backend-developer", context)
        assert result is not None

        # Log fallback
        handler.log_fallback("backend-developer", reason, context, success=True)

        # Verify logging
        assert (tmp_path / "logs" / "fallback.log").exists()
        assert (tmp_path / "logs" / "metrics.log").exists()

        # Check statistics
        stats = handler.get_statistics()
        assert stats["total_invocations"] == 1
        assert stats["prompt_based_fallbacks"] == 1


# Fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Provide temporary directory for tests"""
    return tmp_path


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
