"""
Fallback Scenarios - Examples and Testing

Demonstrates various fallback scenarios and how the system handles them.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fallback import FallbackHandler, HybridAgentInvoker, FailureReason
from health import HealthMonitor
import json


def scenario_1_sdk_not_installed():
    """
    Scenario 1: SDK Not Installed

    What happens: User tries to run SDK agent but SDK not installed
    Expected: Automatic fallback to prompt-based agent
    """
    print("\n" + "="*70)
    print("SCENARIO 1: SDK Not Installed")
    print("="*70)

    handler = FallbackHandler()

    try:
        # Simulate SDK import error
        raise ImportError("No module named 'anthropic'")

    except Exception as e:
        reason = handler.detect_failure(e)
        print(f"✗ Failure detected: {reason.value}")

        should_fallback = handler.should_fallback("backend-developer", e)
        print(f"→ Should fallback? {should_fallback}")

        if should_fallback:
            print("→ Switching to prompt-based agent...")

            context = {
                "workflow_id": "scenario1",
                "task": "Implement user authentication",
                "requirements": ["JWT tokens", "Password hashing", "Session management"]
            }

            result = handler.call_prompt_agent(
                "backend-developer",
                context,
                "Implement login endpoint with JWT"
            )

            handler.log_fallback(
                "backend-developer",
                reason,
                context,
                success=True
            )

            print("✓ Fallback successful!")
            print(f"\nPrompt-based agent invocation:\n{result}")


def scenario_2_api_key_missing():
    """
    Scenario 2: API Key Missing

    What happens: SDK installed but API key not configured
    Expected: Immediate fallback (no retry)
    """
    print("\n" + "="*70)
    print("SCENARIO 2: API Key Missing")
    print("="*70)

    handler = FallbackHandler()

    try:
        # Simulate API key error
        raise ValueError("api_key is required")

    except Exception as e:
        reason = handler.detect_failure(e)
        print(f"✗ Failure detected: {reason.value}")

        should_fallback = handler.should_fallback("frontend-developer", e)
        print(f"→ Should fallback? {should_fallback} (immediate, no retry)")

        context = {
            "workflow_id": "scenario2",
            "task": "Build user profile component"
        }

        result = handler.call_prompt_agent(
            "frontend-developer",
            context,
            "Build React component for user profile"
        )

        handler.log_fallback("frontend-developer", reason, context, success=True)
        print("✓ Fallback successful (no retry needed)!")


def scenario_3_agent_timeout_with_retry():
    """
    Scenario 3: Agent Timeout (with retry)

    What happens: SDK agent times out
    Expected: Retry 2 times, then fallback
    """
    print("\n" + "="*70)
    print("SCENARIO 3: Agent Timeout (with retry)")
    print("="*70)

    handler = FallbackHandler(enable_retry=True, max_retries=2)

    retry_count = 0
    max_retries = 2

    while retry_count <= max_retries:
        try:
            # Simulate timeout
            raise TimeoutError("Agent execution timed out after 60s")

        except Exception as e:
            reason = handler.detect_failure(e)
            print(f"✗ Attempt {retry_count + 1}: Failure - {reason.value}")

            should_fallback = handler.should_fallback(
                "database-expert",
                e,
                retry_count
            )

            if should_fallback:
                print(f"→ Max retries ({max_retries}) exceeded, falling back...")
                break
            else:
                retry_count += 1
                print(f"→ Retrying ({retry_count}/{max_retries})...")

    # Fallback
    context = {"workflow_id": "scenario3", "task": "Design database schema"}
    result = handler.call_prompt_agent("database-expert", context)

    handler.log_fallback(
        "database-expert",
        reason,
        context,
        retry_count=retry_count,
        success=True
    )

    print("✓ Fallback successful after retries!")


def scenario_4_context_conversion_failure():
    """
    Scenario 4: Context Serialization Failure

    What happens: SDK context cannot be converted to JSON
    Expected: Fallback to text-only communication
    """
    print("\n" + "="*70)
    print("SCENARIO 4: Context Serialization Failure")
    print("="*70)

    handler = FallbackHandler()

    # Create complex context with non-serializable data
    class NonSerializable:
        def __str__(self):
            return "ComplexObject"

    sdk_context = {
        "workflow_id": "scenario4",
        "task": "Test serialization",
        "complex_object": NonSerializable(),
        "normal_data": "This is fine"
    }

    print("→ Attempting to convert SDK context to JSON...")

    context_file = handler.convert_context_to_json(sdk_context, "scenario4")

    if context_file:
        print(f"✓ Context converted successfully: {context_file}")
        print("\nConverted context:")
        with open(context_file, 'r') as f:
            print(json.dumps(json.load(f), indent=2))
    else:
        print("✗ Context conversion failed, using text-only mode")
        print("→ Falling back to text-based communication...")

        text_context = f"Task: {sdk_context['task']}\nData: {sdk_context['normal_data']}"
        print(f"\nText context:\n{text_context}")


def scenario_5_hybrid_workflow():
    """
    Scenario 5: Hybrid Workflow (SDK + Prompt-based)

    What happens: Some agents SDK, some prompt-based
    Expected: Seamless coordination via shared context
    """
    print("\n" + "="*70)
    print("SCENARIO 5: Hybrid Workflow")
    print("="*70)

    handler = FallbackHandler()
    invoker = HybridAgentInvoker(handler)

    workflow = {
        "workflow_id": "scenario5",
        "task": "Build full-stack authentication",
        "agents": [
            ("solution-architect", "SDK"),  # Assumes SDK works
            ("database-expert", "SDK"),     # Assumes SDK works
            ("backend-developer", "SDK"),   # Will fail, fallback
            ("frontend-developer", "prompt"), # Direct prompt-based
        ]
    }

    print(f"Workflow: {workflow['task']}")
    print(f"Agents: {len(workflow['agents'])}")
    print()

    context = {
        "workflow_id": workflow["workflow_id"],
        "task": workflow["task"],
        "agent_results": {}
    }

    for agent_name, agent_type in workflow["agents"]:
        print(f"\n→ Running {agent_name} ({agent_type})...")

        # Auto-detect and invoke
        detected_type = invoker.auto_detect_agent_type(agent_name)
        print(f"  Detected type: {detected_type.value}")

        # Simulate: backend-developer fails, others succeed
        if agent_name == "backend-developer":
            print("  ✗ SDK agent failed (simulated)")
            print("  → Falling back to prompt-based...")

            result_text = handler.call_prompt_agent(agent_name, context)
            result = handler.parse_result(result_text or "")

            handler.log_fallback(
                agent_name,
                FailureReason.AGENT_CRASH,
                context,
                success=True
            )
        else:
            print("  ✓ Agent completed successfully")
            result = {"status": "completed", "agent": agent_name}

        # Update context
        context["agent_results"][agent_name] = result

    print("\n✓ Hybrid workflow completed!")
    print(f"\nContext file: {handler.convert_context_to_json(context)}")


def scenario_6_health_check_before_run():
    """
    Scenario 6: Health Check Before Execution

    What happens: Run health checks before starting workflow
    Expected: Identify issues early, choose appropriate agent type
    """
    print("\n" + "="*70)
    print("SCENARIO 6: Pre-execution Health Check")
    print("="*70)

    monitor = HealthMonitor()

    print("→ Running health checks...")
    report = monitor.run_checks()

    print(f"\nOverall Status: {report['overall_status'].upper()}")
    print(f"Ready for SDK: {report['summary']['ready_for_sdk']}")
    print(f"Ready for Prompt-based: {report['summary']['ready_for_prompt_based']}")

    # Decide which agent type to use
    if report['summary']['ready_for_sdk']:
        print("\n✓ System ready for SDK agents")
        agent_type = "SDK"
    elif report['summary']['ready_for_prompt_based']:
        print("\n⚠ SDK not ready, using prompt-based agents")
        agent_type = "Prompt-based"
    else:
        print("\n✗ System not ready for agent execution")
        print("Issues:")
        for check in report['checks']:
            if check['status'] == 'critical':
                print(f"  - {check['name']}: {check['message']}")
        return

    print(f"\n→ Starting workflow with {agent_type} agents...")


def scenario_7_repeated_failure_alert():
    """
    Scenario 7: Repeated Failure Alert

    What happens: Same agent fails multiple times
    Expected: Alert and investigation recommendation
    """
    print("\n" + "="*70)
    print("SCENARIO 7: Repeated Failure Alert")
    print("="*70)

    handler = FallbackHandler()

    agent_name = "security-auditor"

    # Simulate 5 failures of the same agent
    for i in range(5):
        try:
            raise RuntimeError(f"Security auditor crashed (attempt {i+1})")
        except Exception as e:
            reason = handler.detect_failure(e)
            handler.log_fallback(agent_name, reason, success=False)

            # Check for alert
            alert = handler.alert_on_repeated_failures(agent_name, threshold=3)

            if alert:
                print(f"⚠ ALERT: {agent_name} has failed {i+1} times!")

    print("\n✓ Repeated failure detection working!")
    print("\nStatistics:")
    print(json.dumps(handler.get_statistics(), indent=2))


def run_all_scenarios():
    """Run all fallback scenarios"""
    print("\n" + "#"*70)
    print("# FALLBACK SCENARIOS TEST SUITE")
    print("#"*70)

    scenarios = [
        scenario_1_sdk_not_installed,
        scenario_2_api_key_missing,
        scenario_3_agent_timeout_with_retry,
        scenario_4_context_conversion_failure,
        scenario_5_hybrid_workflow,
        scenario_6_health_check_before_run,
        scenario_7_repeated_failure_alert
    ]

    for scenario in scenarios:
        try:
            scenario()
        except Exception as e:
            print(f"\n✗ Scenario failed: {e}")

    print("\n" + "#"*70)
    print("# TEST SUITE COMPLETE")
    print("#"*70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific scenario
        scenario_num = int(sys.argv[1])
        scenarios = {
            1: scenario_1_sdk_not_installed,
            2: scenario_2_api_key_missing,
            3: scenario_3_agent_timeout_with_retry,
            4: scenario_4_context_conversion_failure,
            5: scenario_5_hybrid_workflow,
            6: scenario_6_health_check_before_run,
            7: scenario_7_repeated_failure_alert
        }
        if scenario_num in scenarios:
            scenarios[scenario_num]()
        else:
            print(f"Invalid scenario number: {scenario_num}")
            print(f"Available: 1-{len(scenarios)}")
    else:
        # Run all scenarios
        run_all_scenarios()
