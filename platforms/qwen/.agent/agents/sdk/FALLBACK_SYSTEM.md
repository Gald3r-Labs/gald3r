# Fallback and Error Handling System

**Task 052 Component: Ensuring System Reliability**

This fallback system ensures that agent workflows **always work**, even when the Anthropic Agent SDK is unavailable or fails. It provides automatic degradation from SDK agents to prompt-based agents with comprehensive error handling and monitoring.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Fallback Scenarios](#fallback-scenarios)
5. [Usage Guide](#usage-guide)
6. [Health Monitoring](#health-monitoring)
7. [Logging and Metrics](#logging-and-metrics)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### Design Philosophy

**Always Functional**: The system must work under all conditions:
- SDK not installed → use prompt-based agents
- API key missing → use prompt-based agents
- Network failure → retry, then fallback
- Agent crash → retry, then fallback
- Context conversion fails → use text-based communication

**Graceful Degradation**: Functionality > features
- SDK agents are optimal but not required
- Prompt-based agents always available
- Hybrid workflows supported

### Key Features

- **Automatic Detection**: Identifies failure types and chooses appropriate response
- **Smart Retry Logic**: Retries transient failures, immediate fallback for permanent issues
- **Context Conversion**: Converts SDK context to JSON for prompt-based agents
- **Health Monitoring**: Proactive checks before execution
- **Comprehensive Logging**: Track all fallback events for analysis
- **Statistics**: Monitor fallback rates and identify problem agents

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Invocation Request                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              HybridAgentInvoker (Entry Point)                │
│  - Auto-detects agent type (SDK vs Prompt-based)            │
│  - Tries SDK first (if available)                           │
│  - Handles fallback automatically                           │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌────────────────────────┐    ┌────────────────────────┐
│   Try SDK Agent        │    │  Health Check          │
│   - Import SDK         │    │  - SDK available?      │
│   - Create agent       │    │  - API key set?        │
│   - Execute with retry │    │  - Network OK?         │
└────────────────────────┘    └────────────────────────┘
            │                               │
            ▼                               ▼
         Success?                      All OK?
            │                               │
      ┌─────┴─────┐                  ┌─────┴─────┐
      │           │                  │           │
     Yes         No                 Yes         No
      │           │                  │           │
      │           └──────────────────┘           │
      │                      │                   │
      ▼                      ▼                   ▼
   Return                Detect            Use Prompt-Based
   Result               Failure                Immediately
                           │
                           ▼
                  ┌─────────────────┐
                  │ FallbackHandler  │
                  │  - Analyze error │
                  │  - Decide action │
                  └─────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    Retry Logic   Context Conversion  Call Prompt Agent
    (transient)      (SDK → JSON)     (fallback)
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                  ┌─────────────────┐
                  │ Prompt-Based    │
                  │ Agent Execution │
                  │ (always works)  │
                  └─────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Log Fallback    │
                  │ Event + Metrics │
                  └─────────────────┘
                           │
                           ▼
                    Return Result
```

---

## Components

### 1. FallbackHandler

**File**: `.cursor/agents/sdk/fallback.py`

Core component that manages fallback logic.

**Key Methods**:

```python
class FallbackHandler:
    def detect_failure(exception) -> FailureReason
        """Analyze exception and categorize"""

    def should_fallback(agent_type, exception, retry_count) -> bool
        """Decide if should retry or fallback"""

    def convert_context_to_json(sdk_context, workflow_id) -> Path
        """Convert SDK context to JSON file"""

    def call_prompt_agent(agent_type, context, task) -> str
        """Invoke prompt-based agent"""

    def parse_result(text_output) -> Dict
        """Parse agent output into structured result"""

    def log_fallback(agent_type, reason, context, success)
        """Log fallback event"""

    def get_statistics() -> Dict
        """Get fallback statistics"""

    def alert_on_repeated_failures(agent_type, threshold) -> bool
        """Alert if agent fails repeatedly"""
```

**Failure Reasons**:
- `SDK_NOT_INSTALLED` - Anthropic SDK not installed
- `API_KEY_MISSING` - API key not configured
- `NETWORK_FAILURE` - Network connectivity issues
- `AGENT_CRASH` - Agent crashed during execution
- `AGENT_TIMEOUT` - Agent execution timed out
- `CONTEXT_SERIALIZATION` - Context conversion failed
- `TOOL_INVOCATION_ERROR` - Tool call failed
- `MEMORY_ERROR` - Memory/resource issue
- `UNKNOWN` - Unclassified error

### 2. HybridAgentInvoker

**File**: `.cursor/agents/sdk/fallback.py`

Unified interface for invoking agents with automatic fallback.

**Usage**:

```python
from fallback import HybridAgentInvoker

invoker = HybridAgentInvoker()

# Automatically tries SDK, falls back to prompt-based if needed
result = invoker.invoke(
    agent_name="backend-developer",
    context={"task": "Build login API"},
    task="Implement JWT authentication"
)
```

**Methods**:

```python
class HybridAgentInvoker:
    def auto_detect_agent_type(agent_name) -> AgentType
        """Detect if agent is SDK or prompt-based"""

    def invoke(agent_name, context, task, prefer_sdk=True) -> Dict
        """Invoke agent with automatic fallback"""
```

### 3. HealthMonitor

**File**: `.cursor/agents/sdk/health.py`

Proactive health checks to identify issues before execution.

**Health Checks**:
1. **SDK Availability** - Is SDK installed and importable?
2. **API Key** - Is ANTHROPIC_API_KEY configured?
3. **Agent Files** - Do agent files exist?
4. **Context Storage** - Can we write to context directory?
5. **System Resources** - Enough memory/disk?
6. **Network** - Can we reach Anthropic API?

**Usage**:

```python
from health import HealthMonitor

monitor = HealthMonitor()

# Run all checks
report = monitor.run_checks()

# Print report
monitor.print_report(report)

# Check if ready
ready, issues = monitor.get_agent_readiness()
if not ready:
    print("Issues:", issues)

# Validate specific agent
valid, message = monitor.validate_agent("backend-developer")
```

**CLI Usage**:

```bash
# Full health check
python .cursor/agents/sdk/health.py

# Check readiness
python .cursor/agents/sdk/health.py readiness

# Validate agent
python .cursor/agents/sdk/health.py validate backend-developer
```

---

## Fallback Scenarios

### Scenario 1: SDK Not Installed

**Situation**: User runs workflow, but SDK not installed

**Detection**: `ImportError: No module named 'anthropic'`

**Action**: Immediate fallback (no retry)

**Flow**:
1. Try to import SDK → fails
2. Detect `SDK_NOT_INSTALLED`
3. Convert context to JSON
4. Call prompt-based agent
5. Log fallback event

**Example**:

```python
try:
    from anthropic import Agent
    # Create SDK agent
except ImportError:
    # Fallback to prompt-based
    handler.call_prompt_agent("backend-developer", context)
```

### Scenario 2: API Key Missing

**Situation**: SDK installed but `ANTHROPIC_API_KEY` not set

**Detection**: Authentication error or missing API key

**Action**: Immediate fallback (no retry)

**Flow**:
1. SDK imported successfully
2. Try to create agent → API key error
3. Detect `API_KEY_MISSING`
4. Fallback to prompt-based agent

### Scenario 3: Network Failure

**Situation**: Network connectivity issues

**Detection**: Connection timeout, network unreachable

**Action**: Retry 2 times, then fallback

**Flow**:
1. SDK agent starts execution
2. Network request fails
3. Detect `NETWORK_FAILURE`
4. Retry (attempt 1)
5. Still fails → Retry (attempt 2)
6. Still fails → Fallback to prompt-based

**Configuration**:

```python
handler = FallbackHandler(
    enable_retry=True,
    max_retries=2  # Retry twice before fallback
)
```

### Scenario 4: Agent Crash

**Situation**: Agent crashes during execution

**Detection**: RuntimeError, SystemError, uncaught exception

**Action**: Retry 2 times, then fallback

**Flow**:
1. SDK agent executing
2. Agent crashes (e.g., invalid tool call)
3. Detect `AGENT_CRASH`
4. Retry with same context
5. If still crashes → Fallback

### Scenario 5: Context Serialization Failure

**Situation**: SDK context cannot be converted to JSON

**Detection**: JSON serialization error

**Action**: Use text-based communication

**Flow**:
1. Try to convert SDK context to JSON
2. Fails (e.g., non-serializable object)
3. Detect `CONTEXT_SERIALIZATION`
4. Extract what we can as strings
5. Pass text description to prompt-based agent

**Example**:

```python
# SDK context has complex objects
sdk_context = {
    "workflow_id": "123",
    "complex_object": NonSerializableClass(),
    "task": "Build feature"
}

# Conversion attempts extraction
context_json = handler.convert_context_to_json(sdk_context)
# Extracts: {"workflow_id": "123", "task": "Build feature",
#            "raw_context": "ComplexObject"}
```

### Scenario 6: Hybrid Workflow

**Situation**: Mix of SDK and prompt-based agents in one workflow

**Detection**: Auto-detect per agent

**Action**: Use appropriate type for each agent

**Flow**:
1. Workflow has 5 agents
2. Agent 1 (SDK) → executes with SDK
3. Agent 2 (prompt-based) → executes with Task tool
4. Agent 3 (SDK fails) → fallback to prompt-based
5. All agents share context via JSON files

**Example**:

```python
workflow = [
    ("solution-architect", "SDK"),     # SDK agent
    ("backend-developer", "SDK"),      # SDK agent (may fallback)
    ("frontend-developer", "prompt"),  # Direct prompt-based
]

for agent_name, preferred_type in workflow:
    result = invoker.invoke(agent_name, context)
    # Automatically uses appropriate type
```

### Scenario 7: Repeated Failures

**Situation**: Same agent fails multiple times

**Detection**: Statistics tracking

**Action**: Alert and recommend investigation

**Flow**:
1. Agent fails
2. Log failure
3. Check failure count for this agent
4. If ≥ threshold (default 3) → Alert

**Example**:

```python
# After 3rd failure
handler.log_fallback("security-auditor", reason)

alert = handler.alert_on_repeated_failures("security-auditor", threshold=3)
if alert:
    print("⚠ ALERT: security-auditor has failed 3+ times!")
    print("Investigation recommended:")
    print("- Check agent configuration")
    print("- Review logs")
    print("- Validate agent file")
```

---

## Usage Guide

### Basic Usage

```python
from fallback import HybridAgentInvoker

# Initialize invoker
invoker = HybridAgentInvoker()

# Invoke agent (automatic fallback)
result = invoker.invoke(
    agent_name="backend-developer",
    context={"task": "Build API"},
    task="Implement user endpoints"
)

print(result)
```

### Advanced Configuration

```python
from fallback import FallbackHandler, HybridAgentInvoker

# Configure fallback behavior
handler = FallbackHandler(
    log_dir=Path(".cursor/agents/sdk/logs"),
    enable_retry=True,
    max_retries=3,
    context_dir=Path(".cursor/agent_context/json")
)

# Use custom handler
invoker = HybridAgentInvoker(fallback_handler=handler)

result = invoker.invoke("backend-developer", context)
```

### Pre-execution Health Check

```python
from health import HealthMonitor

monitor = HealthMonitor()

# Check before running workflow
ready, issues = monitor.get_agent_readiness()

if ready:
    # Proceed with workflow
    result = invoker.invoke("backend-developer", context)
else:
    print("System not ready:")
    for issue in issues:
        print(f"  - {issue}")
    # Fix issues or use prompt-based only
```

### Context Conversion

```python
from fallback import FallbackHandler

handler = FallbackHandler()

# Convert SDK context to JSON for prompt-based agents
sdk_context = {
    "workflow_id": "123",
    "task": "Build feature",
    "shared_artifacts": {...}
}

context_file = handler.convert_context_to_json(sdk_context)
print(f"Context saved to: {context_file}")

# Prompt-based agent can read this file
# Then write back to same file with results
```

### Manual Fallback

```python
from fallback import FallbackHandler

handler = FallbackHandler()

try:
    # Try SDK agent
    result = run_sdk_agent("backend-developer", context)

except Exception as e:
    # Manual fallback
    reason = handler.detect_failure(e)

    if handler.should_fallback("backend-developer", e):
        result = handler.call_prompt_agent(
            "backend-developer",
            context,
            "Build login API"
        )

        handler.log_fallback("backend-developer", reason, context, success=True)
```

---

## Health Monitoring

### Running Health Checks

**Python API**:

```python
from health import HealthMonitor

monitor = HealthMonitor()

# Full health check
report = monitor.run_checks()

# Print to console
monitor.print_report(report)

# Access specific results
if report['overall_status'] == 'healthy':
    print("All systems go!")
else:
    # Check individual failures
    for check in report['checks']:
        if check['status'] != 'healthy':
            print(f"Issue: {check['name']} - {check['message']}")
```

**CLI**:

```bash
# Full report
python .cursor/agents/sdk/health.py

# Readiness check (exit code 0 = ready, 1 = not ready)
python .cursor/agents/sdk/health.py readiness

# Validate specific agent
python .cursor/agents/sdk/health.py validate backend-developer
```

### Health Check Results

```json
{
  "timestamp": "2025-11-01T12:00:00Z",
  "overall_status": "healthy",
  "checks": [
    {
      "name": "sdk_availability",
      "status": "healthy",
      "message": "SDK available",
      "details": {
        "installed": true,
        "version": "0.40.0"
      }
    },
    {
      "name": "api_key",
      "status": "healthy",
      "message": "API key configured"
    }
  ],
  "summary": {
    "total_checks": 6,
    "status_counts": {
      "healthy": 6,
      "warning": 0,
      "critical": 0
    },
    "ready_for_sdk": true,
    "ready_for_prompt_based": true
  }
}
```

### Interpreting Results

**overall_status**:
- `healthy`: All checks passed, SDK ready
- `warning`: Some issues, SDK may work but with degraded performance
- `critical`: Major issues, SDK will not work (use prompt-based)

**ready_for_sdk**: Can we use SDK agents?
- `true`: Yes, all SDK dependencies met
- `false`: No, use prompt-based agents

**ready_for_prompt_based**: Can we use prompt-based agents?
- `true`: Yes, basic requirements met (always should be true)
- `false`: Severe system issues

---

## Logging and Metrics

### Log Files

**Location**: `.cursor/agents/sdk/logs/`

**Files**:
- `fallback.log` - Detailed fallback events
- `metrics.log` - Structured metrics (JSONL)
- `health.log` - Health check results
- `latest_health.json` - Most recent health report
- `health_history.jsonl` - Health check history

### Fallback Log Format

```
2025-11-01 12:05:00 - FallbackHandler - WARNING - [backend-developer] SDK agent failed: SDK timeout
2025-11-01 12:05:01 - FallbackHandler - INFO - [backend-developer] Retry 1/2: agent_timeout
2025-11-01 12:05:05 - FallbackHandler - WARNING - [backend-developer] Max retries exceeded, falling back: agent_timeout
2025-11-01 12:05:06 - FallbackHandler - INFO - Context converted to JSON: .cursor/agent_context/json/123.json
2025-11-01 12:05:07 - FallbackHandler - INFO - Invoking prompt-based agent: backend-developer
2025-11-01 12:05:20 - FallbackHandler - INFO - Fallback event: {"timestamp": "...", "agent_type": "backend-developer", "success": true}
```

### Metrics Format

**metrics.log** (JSONL):

```json
{"timestamp": "2025-11-01T12:05:20Z", "agent_type": "backend-developer", "failure_reason": "agent_timeout", "retry_count": 2, "success": true, "workflow_id": "123"}
{"timestamp": "2025-11-01T12:10:15Z", "agent_type": "frontend-developer", "failure_reason": "sdk_not_installed", "retry_count": 0, "success": true, "workflow_id": "124"}
```

### Statistics

```python
stats = handler.get_statistics()
```

**Output**:

```json
{
  "total_invocations": 100,
  "sdk_successes": 75,
  "sdk_failures": 25,
  "prompt_based_fallbacks": 25,
  "fallback_rate": 0.25,
  "sdk_success_rate": 0.75,
  "failure_reasons": {
    "agent_timeout": 10,
    "sdk_not_installed": 8,
    "network_failure": 5,
    "agent_crash": 2
  },
  "agents_failed": {
    "backend-developer": 8,
    "security-auditor": 7,
    "frontend-developer": 5,
    "database-expert": 5
  }
}
```

### Analyzing Metrics

**High fallback rate** (>30%):
- Check SDK installation
- Validate API key
- Check network connectivity
- Review agent configurations

**Specific agent failing repeatedly**:
- Review agent code
- Check dependencies
- Validate prompts
- Test in isolation

**Specific failure reason dominant**:
- `sdk_not_installed` → Install SDK
- `api_key_missing` → Configure API key
- `network_failure` → Check internet connection
- `agent_timeout` → Increase timeout or optimize agent

---

## Best Practices

### 1. Always Use HybridAgentInvoker

**Do**:
```python
invoker = HybridAgentInvoker()
result = invoker.invoke("backend-developer", context)
```

**Don't**:
```python
# Directly calling SDK agent without fallback
agent = BackendDeveloper()
result = agent.run(context)  # No fallback if fails!
```

### 2. Run Health Checks in CI/CD

```yaml
# .github/workflows/health-check.yml
- name: Check Agent Health
  run: |
    python .cursor/agents/sdk/health.py readiness
    if [ $? -ne 0 ]; then
      echo "Agent system not ready!"
      exit 1
    fi
```

### 3. Monitor Fallback Rates

```python
# Periodic check
stats = handler.get_statistics()
if stats['fallback_rate'] > 0.3:
    print("⚠ High fallback rate! Investigate:")
    print(f"  Top failures: {stats['failure_reasons']}")
```

### 4. Set Up Alerts

```python
# Alert on repeated failures
for agent in ["backend-developer", "frontend-developer"]:
    if handler.alert_on_repeated_failures(agent, threshold=3):
        # Send alert (email, Slack, etc.)
        send_alert(f"Agent {agent} failing repeatedly!")
```

### 5. Test Fallback Scenarios

```bash
# Run test suite
python .cursor/agents/sdk/examples/fallback_scenarios.py
```

### 6. Keep Prompt-Based Agents Updated

Even with SDK agents, maintain prompt-based versions:
- They're your fallback
- They should be functionally equivalent
- Test them regularly

### 7. Log Context Conversions

Always log when converting SDK context to JSON:
```python
context_file = handler.convert_context_to_json(sdk_context)
logger.info(f"Context converted for fallback: {context_file}")
```

### 8. Clean Up Old Contexts

```bash
# Cleanup old context files (>7 days)
find .cursor/agent_context/json -type f -mtime +7 -delete
```

---

## Troubleshooting

### Problem: Fallback not working

**Symptoms**: Both SDK and prompt-based agents fail

**Causes**:
1. Prompt-based agent files missing
2. Context directory not writable
3. Severe system issues

**Solutions**:
```bash
# Check agent files
ls -la .cursor/agents/prompt-based/

# Check permissions
ls -la .cursor/agent_context/

# Run health check
python .cursor/agents/sdk/health.py
```

### Problem: High fallback rate

**Symptoms**: >30% of invocations fall back

**Causes**:
1. SDK not installed
2. Network issues
3. API key problems
4. Agent code bugs

**Solutions**:
```python
# Check statistics
stats = handler.get_statistics()
print(f"Top failure: {max(stats['failure_reasons'], key=stats['failure_reasons'].get)}")

# Run health check
monitor = HealthMonitor()
report = monitor.run_checks()
```

### Problem: Context conversion fails

**Symptoms**: Cannot convert SDK context to JSON

**Causes**:
1. Non-serializable objects in context
2. Circular references
3. Large binary data

**Solutions**:
```python
# Clean context before conversion
clean_context = {
    k: v for k, v in sdk_context.items()
    if isinstance(v, (str, int, float, bool, dict, list))
}

context_file = handler.convert_context_to_json(clean_context)
```

### Problem: Repeated agent failures

**Symptoms**: Same agent fails consistently

**Causes**:
1. Agent code bug
2. Missing dependencies
3. Invalid configuration
4. Resource constraints

**Solutions**:
```bash
# Validate agent
python .cursor/agents/sdk/health.py validate backend-developer

# Check logs
tail -f .cursor/agents/sdk/logs/fallback.log

# Test in isolation
python -c "from sdk.agents.backend_developer import BackendDeveloper; agent = BackendDeveloper()"
```

### Problem: SDK installed but not detected

**Symptoms**: Health check says SDK not available

**Causes**:
1. Wrong Python environment
2. Import path issues
3. Version mismatch

**Solutions**:
```bash
# Check Python environment
which python
python -c "import anthropic; print(anthropic.__version__)"

# Check installation
pip show anthropic

# Reinstall
pip install --upgrade anthropic>=0.40.0
```

---

## Examples

### Example 1: Basic Workflow with Fallback

```python
from fallback import HybridAgentInvoker
from health import HealthMonitor

# Health check
monitor = HealthMonitor()
ready, issues = monitor.get_agent_readiness()

if not ready:
    print("Issues detected:", issues)

# Run workflow with automatic fallback
invoker = HybridAgentInvoker()

context = {
    "workflow_id": "auth-feature",
    "task": "Implement authentication"
}

# These will automatically fallback if SDK unavailable
result1 = invoker.invoke("backend-developer", context, "Build login API")
result2 = invoker.invoke("frontend-developer", context, "Build login UI")
result3 = invoker.invoke("database-expert", context, "Design user schema")

print("Workflow complete!")
```

### Example 2: Custom Retry Logic

```python
from fallback import FallbackHandler

# Custom retry configuration
handler = FallbackHandler(
    enable_retry=True,
    max_retries=5,  # Retry 5 times for network issues
)

# Use in workflow
# handler will retry 5 times before falling back
```

### Example 3: Monitoring Dashboard

```python
from fallback import FallbackHandler
import time

handler = FallbackHandler()

# Periodic statistics
while True:
    stats = handler.get_statistics()

    print("\n=== Agent Statistics ===")
    print(f"Total invocations: {stats['total_invocations']}")
    print(f"SDK success rate: {stats['sdk_success_rate']:.1%}")
    print(f"Fallback rate: {stats['fallback_rate']:.1%}")
    print(f"\nTop failures:")
    for reason, count in sorted(stats['failure_reasons'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {reason}: {count}")

    time.sleep(60)  # Update every minute
```

---

## Success Criteria

- ✅ FallbackHandler implemented and tested
- ✅ Auto-detection of agent type (SDK vs prompt-based)
- ✅ Graceful degradation (system always works)
- ✅ Comprehensive logging (all events tracked)
- ✅ Health monitoring (proactive issue detection)
- ✅ Examples and scenarios documented
- ✅ Statistics and metrics collection
- ✅ Repeated failure alerts

---

## Files Created

```
.cursor/agents/sdk/
├── fallback.py                      # Core fallback handler
├── health.py                        # Health monitoring system
├── FALLBACK_SYSTEM.md              # This documentation
├── examples/
│   └── fallback_scenarios.py       # Test scenarios
└── logs/                           # Created automatically
    ├── fallback.log
    ├── metrics.log
    ├── health.log
    ├── latest_health.json
    └── health_history.jsonl
```

---

## Next Steps

1. **Integration**: Other Task 052 components will integrate with this fallback system
2. **Testing**: Run fallback scenarios to validate behavior
3. **Monitoring**: Set up periodic health checks
4. **Optimization**: Tune retry counts and thresholds based on real usage

---

**Task 052 Component**: Fallback and Error Handling ✅ Complete

This system ensures that agent workflows are resilient and always functional, regardless of SDK availability or transient failures.
