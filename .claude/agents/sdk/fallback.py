"""
Fallback Handler for Anthropic Agent SDK Integration

Provides robust fallback mechanisms to ensure the system always works:
- SDK unavailable → prompt-based agents
- SDK agent failure → retry with prompt-based
- Context conversion failure → text-based communication
"""

import logging
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum


class FailureReason(Enum):
    """Categorize failure reasons for analytics"""
    SDK_NOT_INSTALLED = "sdk_not_installed"
    SDK_IMPORT_ERROR = "sdk_import_error"
    API_KEY_MISSING = "api_key_missing"
    NETWORK_FAILURE = "network_failure"
    AGENT_CRASH = "agent_crash"
    AGENT_TIMEOUT = "agent_timeout"
    CONTEXT_SERIALIZATION = "context_serialization"
    CONTEXT_DESERIALIZATION = "context_deserialization"
    TOOL_INVOCATION_ERROR = "tool_invocation_error"
    MEMORY_ERROR = "memory_error"
    UNKNOWN = "unknown"


class AgentType(Enum):
    """Agent execution modes"""
    SDK = "sdk"
    PROMPT_BASED = "prompt_based"
    HYBRID = "hybrid"


class FallbackHandler:
    """
    Manages fallback from SDK agents to prompt-based agents

    Ensures the system is resilient and always functional, even if
    the Agent SDK is unavailable or fails.
    """

    def __init__(self,
                 log_dir: Path = None,
                 enable_retry: bool = True,
                 max_retries: int = 2,
                 context_dir: Path = None):
        """
        Initialize fallback handler

        Args:
            log_dir: Directory for fallback logs
            enable_retry: Whether to retry failed SDK agents
            max_retries: Maximum retry attempts before fallback
            context_dir: Directory for context JSON files
        """
        self.log_dir = log_dir or Path(".claude/agents/sdk/logs")
        self.context_dir = context_dir or Path(".claude/agent_context/json")
        self.enable_retry = enable_retry
        self.max_retries = max_retries

        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = self._setup_logger()

        # Statistics
        self.stats = {
            "total_invocations": 0,
            "sdk_successes": 0,
            "sdk_failures": 0,
            "prompt_based_fallbacks": 0,
            "failure_reasons": {},
            "agents_failed": {}
        }

    def _setup_logger(self) -> logging.Logger:
        """Setup fallback logging"""
        logger = logging.getLogger("FallbackHandler")
        logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler(self.log_dir / "fallback.log")
        fh.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def detect_failure(self, exception: Exception) -> FailureReason:
        """
        Analyze exception to determine failure reason

        Args:
            exception: Exception that occurred

        Returns:
            Categorized failure reason
        """
        exc_str = str(exception).lower()
        exc_type = type(exception).__name__

        # SDK not installed
        if "no module named 'anthropic'" in exc_str or isinstance(exception, ImportError):
            return FailureReason.SDK_NOT_INSTALLED

        # API key missing
        if "api_key" in exc_str or "authentication" in exc_str:
            return FailureReason.API_KEY_MISSING

        # Network issues
        if "connection" in exc_str or "timeout" in exc_str or "network" in exc_str:
            return FailureReason.NETWORK_FAILURE

        # Timeout
        if "timeout" in exc_str or isinstance(exception, TimeoutError):
            return FailureReason.AGENT_TIMEOUT

        # Context serialization
        if "json" in exc_str or "serialize" in exc_str:
            return FailureReason.CONTEXT_SERIALIZATION

        # Memory errors
        if "memory" in exc_str:
            return FailureReason.MEMORY_ERROR

        # Tool errors
        if "tool" in exc_str:
            return FailureReason.TOOL_INVOCATION_ERROR

        # Agent crash
        if "crash" in exc_str or isinstance(exception, (RuntimeError, SystemError)):
            return FailureReason.AGENT_CRASH

        return FailureReason.UNKNOWN

    def should_fallback(self,
                       agent_type: str,
                       exception: Exception,
                       retry_count: int = 0) -> bool:
        """
        Determine if we should fallback to prompt-based agent

        Args:
            agent_type: Agent that failed
            exception: Exception that occurred
            retry_count: Current retry attempt

        Returns:
            True if should fallback, False if should retry
        """
        failure_reason = self.detect_failure(exception)

        # Always fallback for these reasons (no retry)
        no_retry_reasons = [
            FailureReason.SDK_NOT_INSTALLED,
            FailureReason.API_KEY_MISSING
        ]

        if failure_reason in no_retry_reasons:
            self.logger.warning(
                f"[{agent_type}] Immediate fallback: {failure_reason.value}"
            )
            return True

        # Retry if enabled and under limit
        if self.enable_retry and retry_count < self.max_retries:
            self.logger.info(
                f"[{agent_type}] Retry {retry_count + 1}/{self.max_retries}: {failure_reason.value}"
            )
            return False

        # Fallback after max retries
        self.logger.warning(
            f"[{agent_type}] Max retries exceeded, falling back: {failure_reason.value}"
        )
        return True

    def convert_context_to_json(self,
                               sdk_context: Any,
                               workflow_id: str = None) -> Optional[Path]:
        """
        Convert SDK context to JSON file for prompt-based agents

        Args:
            sdk_context: Agent SDK context object
            workflow_id: Workflow identifier

        Returns:
            Path to JSON context file, or None if conversion failed
        """
        try:
            # Generate workflow ID if not provided
            if workflow_id is None:
                workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            context_file = self.context_dir / f"{workflow_id}.json"

            # Try to extract data from SDK context
            context_data = {}

            # Handle different SDK context types
            if hasattr(sdk_context, '__dict__'):
                # Object with attributes
                context_data = {
                    k: v for k, v in sdk_context.__dict__.items()
                    if not k.startswith('_')
                }
            elif hasattr(sdk_context, 'to_dict'):
                # Has to_dict method
                context_data = sdk_context.to_dict()
            elif isinstance(sdk_context, dict):
                # Already a dict
                context_data = sdk_context
            else:
                # Fallback: convert to string
                context_data = {"raw_context": str(sdk_context)}

            # Add metadata
            context_data['_metadata'] = {
                'workflow_id': workflow_id,
                'converted_at': datetime.now().isoformat(),
                'agent_mode': 'prompt_based_fallback',
                'original_type': type(sdk_context).__name__
            }

            # Write JSON file
            with open(context_file, 'w') as f:
                json.dump(context_data, f, indent=2, default=str)

            self.logger.info(f"Context converted to JSON: {context_file}")
            return context_file

        except Exception as e:
            self.logger.error(f"Context conversion failed: {e}")
            self.logger.debug(traceback.format_exc())
            return None

    def convert_json_to_context(self, json_file: Path) -> Optional[Dict[str, Any]]:
        """
        Load JSON context file into dict

        Args:
            json_file: Path to JSON context file

        Returns:
            Context dictionary or None if failed
        """
        try:
            with open(json_file, 'r') as f:
                context_data = json.load(f)
            return context_data

        except Exception as e:
            self.logger.error(f"Failed to load JSON context: {e}")
            return None

    def call_prompt_agent(self,
                         agent_type: str,
                         context: Union[Dict, Path, Any],
                         task_description: str = None) -> Optional[str]:
        """
        Invoke prompt-based agent as fallback

        Args:
            agent_type: Agent name (e.g., "backend-developer")
            context: Context (dict, file path, or SDK context)
            task_description: Task description

        Returns:
            Agent output as text, or None if failed
        """
        try:
            # Convert context if needed
            if not isinstance(context, (dict, Path)):
                context_file = self.convert_context_to_json(context)
                if context_file is None:
                    self.logger.error("Context conversion failed, using text-only mode")
                    context = {"task": task_description or "No context available"}
                    context_file = self.convert_context_to_json(context)
            elif isinstance(context, dict):
                context_file = self.convert_context_to_json(context)
            else:
                context_file = context

            # Build prompt for agent
            agent_file = Path(f".claude/agents/prompt-based/{agent_type}.md")

            if not agent_file.exists():
                # Try without hyphen
                agent_file = Path(f".claude/agents/{agent_type}.md")

            if not agent_file.exists():
                self.logger.error(f"Prompt-based agent not found: {agent_type}")
                return None

            # Construct invocation message
            invocation_msg = f"""
[FALLBACK MODE - Using prompt-based agent]

Agent: {agent_type}
Context file: {context_file}
Task: {task_description or 'See context file'}

Please read the context file at {context_file} to see:
- Workflow state
- Completed agents
- Shared artifacts
- Your specific task

After completing your work, update the context file with your results.
This ensures other agents can see your work!
"""

            self.logger.info(f"Invoking prompt-based agent: {agent_type}")

            # In real implementation, this would use Cursor's Task tool
            # For now, return instruction message
            return invocation_msg

        except Exception as e:
            self.logger.error(f"Prompt agent invocation failed: {e}")
            self.logger.debug(traceback.format_exc())
            return None

    def parse_result(self, text_output: str) -> Dict[str, Any]:
        """
        Parse text output from prompt-based agent into structured result

        Args:
            text_output: Agent's text output

        Returns:
            Structured result dictionary
        """
        result = {
            "status": "completed",
            "raw_output": text_output,
            "structured_data": {}
        }

        try:
            # Try to extract JSON from output
            # Look for JSON blocks
            if "```json" in text_output:
                start = text_output.find("```json") + 7
                end = text_output.find("```", start)
                if end > start:
                    json_str = text_output[start:end].strip()
                    result["structured_data"] = json.loads(json_str)

            # Look for key-value patterns
            elif ":" in text_output:
                lines = text_output.split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        result["structured_data"][key.strip()] = value.strip()

        except Exception as e:
            self.logger.warning(f"Could not parse structured data from output: {e}")

        return result

    def log_fallback(self,
                    agent_type: str,
                    failure_reason: FailureReason,
                    context: Dict[str, Any] = None,
                    retry_count: int = 0,
                    success: bool = False):
        """
        Log fallback event for analytics

        Args:
            agent_type: Agent that failed/succeeded
            failure_reason: Why fallback occurred
            context: Context data
            retry_count: Number of retries attempted
            success: Whether fallback succeeded
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "agent_type": agent_type,
            "failure_reason": failure_reason.value,
            "retry_count": retry_count,
            "success": success,
            "workflow_id": context.get('workflow_id') if context else None
        }

        # Update statistics
        self.stats["total_invocations"] += 1
        if success:
            self.stats["prompt_based_fallbacks"] += 1
        else:
            self.stats["sdk_failures"] += 1

        # Track failure reasons
        reason_key = failure_reason.value
        self.stats["failure_reasons"][reason_key] = \
            self.stats["failure_reasons"].get(reason_key, 0) + 1

        # Track agents that fail
        self.stats["agents_failed"][agent_type] = \
            self.stats["agents_failed"].get(agent_type, 0) + 1

        # Write to log
        self.logger.info(f"Fallback event: {json.dumps(event)}")

        # Write to metrics log
        metrics_file = self.log_dir / "metrics.log"
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get fallback statistics

        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            "fallback_rate": (
                self.stats["prompt_based_fallbacks"] / self.stats["total_invocations"]
                if self.stats["total_invocations"] > 0 else 0
            ),
            "sdk_success_rate": (
                self.stats["sdk_successes"] / self.stats["total_invocations"]
                if self.stats["total_invocations"] > 0 else 0
            )
        }

    def alert_on_repeated_failures(self,
                                  agent_type: str,
                                  threshold: int = 3) -> bool:
        """
        Check if agent has failed repeatedly and should be investigated

        Args:
            agent_type: Agent to check
            threshold: Failure count threshold

        Returns:
            True if alert threshold exceeded
        """
        failure_count = self.stats["agents_failed"].get(agent_type, 0)

        if failure_count >= threshold:
            self.logger.warning(
                f"ALERT: Agent '{agent_type}' has failed {failure_count} times! "
                f"Investigation recommended."
            )
            return True

        return False


class HybridAgentInvoker:
    """
    Unified agent invoker that auto-detects and uses SDK or prompt-based agents

    Provides transparent fallback: tries SDK first, falls back to prompt-based
    """

    def __init__(self, fallback_handler: FallbackHandler = None):
        """
        Initialize hybrid invoker

        Args:
            fallback_handler: FallbackHandler instance
        """
        self.fallback = fallback_handler or FallbackHandler()
        self.logger = logging.getLogger("HybridAgentInvoker")

    def auto_detect_agent_type(self, agent_name: str) -> AgentType:
        """
        Auto-detect if agent is SDK or prompt-based

        Args:
            agent_name: Agent to check

        Returns:
            Agent type
        """
        # Check if SDK agent exists
        sdk_agent_file = Path(f".claude/agents/sdk/agents/{agent_name}.py")
        if sdk_agent_file.exists():
            # Check if SDK is available
            try:
                import anthropic
                return AgentType.SDK
            except ImportError:
                self.logger.warning("SDK not available, using prompt-based")

        # Check if prompt-based agent exists
        prompt_agent_file = Path(f".claude/agents/prompt-based/{agent_name}.md")
        if prompt_agent_file.exists():
            return AgentType.PROMPT_BASED

        # Fallback
        return AgentType.PROMPT_BASED

    def invoke(self,
              agent_name: str,
              context: Any,
              task: str = None,
              prefer_sdk: bool = True) -> Dict[str, Any]:
        """
        Invoke agent with automatic fallback

        Args:
            agent_name: Agent to invoke
            context: Context data
            task: Task description
            prefer_sdk: Try SDK first if available

        Returns:
            Agent result
        """
        retry_count = 0
        result = None

        # Detect agent type
        agent_type = self.auto_detect_agent_type(agent_name)

        # Try SDK agent first if preferred and available
        if prefer_sdk and agent_type == AgentType.SDK:
            while retry_count <= self.fallback.max_retries:
                try:
                    result = self._invoke_sdk_agent(agent_name, context, task)
                    self.fallback.stats["sdk_successes"] += 1
                    return result

                except Exception as e:
                    failure_reason = self.fallback.detect_failure(e)

                    if self.fallback.should_fallback(agent_name, e, retry_count):
                        self.logger.warning(
                            f"SDK agent failed, falling back to prompt-based: {e}"
                        )
                        break
                    else:
                        retry_count += 1

            # Log fallback
            self.fallback.log_fallback(
                agent_type=agent_name,
                failure_reason=failure_reason,
                context=context if isinstance(context, dict) else None,
                retry_count=retry_count
            )

        # Fallback to prompt-based agent
        try:
            result = self._invoke_prompt_agent(agent_name, context, task)
            self.fallback.log_fallback(
                agent_type=agent_name,
                failure_reason=FailureReason.UNKNOWN,
                context=context if isinstance(context, dict) else None,
                success=True
            )
            return result

        except Exception as e:
            self.logger.error(f"Prompt-based agent also failed: {e}")
            self.fallback.log_fallback(
                agent_type=agent_name,
                failure_reason=self.fallback.detect_failure(e),
                context=context if isinstance(context, dict) else None,
                success=False
            )
            raise

    def _invoke_sdk_agent(self,
                         agent_name: str,
                         context: Any,
                         task: str) -> Dict[str, Any]:
        """Invoke SDK agent (placeholder for actual SDK integration)"""
        # This would import and invoke the actual SDK agent
        # For now, simulate
        raise NotImplementedError("SDK agent invocation not yet implemented")

    def _invoke_prompt_agent(self,
                           agent_name: str,
                           context: Any,
                           task: str) -> Dict[str, Any]:
        """Invoke prompt-based agent"""
        output = self.fallback.call_prompt_agent(agent_name, context, task)
        if output is None:
            raise RuntimeError(f"Prompt agent invocation failed: {agent_name}")

        result = self.fallback.parse_result(output)
        return result


# Example usage
if __name__ == "__main__":
    # Initialize fallback handler
    handler = FallbackHandler()

    # Simulate SDK failure
    try:
        # SDK agent would be called here
        raise ImportError("No module named 'anthropic'")
    except Exception as e:
        reason = handler.detect_failure(e)
        print(f"Failure detected: {reason.value}")

        if handler.should_fallback("backend-developer", e):
            # Fallback to prompt-based
            context = {
                "workflow_id": "test-123",
                "task": "Implement user authentication"
            }

            result = handler.call_prompt_agent(
                "backend-developer",
                context,
                "Implement login endpoint"
            )

            handler.log_fallback(
                "backend-developer",
                reason,
                context,
                success=True
            )

    # Print statistics
    print("\nFallback Statistics:")
    print(json.dumps(handler.get_statistics(), indent=2))
