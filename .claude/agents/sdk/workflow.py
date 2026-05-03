"""
AgentWorkflow: Orchestrate multi-agent workflows

Supports sequential, parallel, and conditional agent execution
with error handling, retry logic, and progress tracking.
"""

from typing import Any, Dict, List, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime
from pathlib import Path

from .context import AgentContext
from .base_agent import BaseAgent


class AgentWorkflow:
    """
    Orchestrator for multi-agent workflows.

    Supports:
    - Sequential agent execution
    - Parallel agent execution
    - Conditional branching
    - Error handling and retry
    - Progress tracking
    - Context management

    Example:
        ```python
        # Sequential workflow
        workflow = AgentWorkflow()
        context = workflow.create_context(task="Build authentication")

        result = workflow.run_sequential([
            ("database-expert", database_agent),
            ("backend-developer", backend_agent),
            ("frontend-developer", frontend_agent)
        ], context)

        # Parallel workflow
        result = workflow.run_parallel([
            ("backend-service-1", backend_agent_1),
            ("backend-service-2", backend_agent_2),
            ("backend-service-3", backend_agent_3)
        ], context)

        # Conditional workflow
        def should_run_security_audit(ctx):
            return ctx.get("api_endpoints", []) and ctx.get("handles_auth", False)

        result = workflow.run_conditional([
            ("backend-developer", backend_agent, None),
            ("security-auditor", security_agent, should_run_security_audit),
            ("frontend-developer", frontend_agent, None)
        ], context)
        ```
    """

    def __init__(
        self,
        max_parallel_agents: int = 5,
        enable_progress_tracking: bool = True
    ):
        """
        Initialize workflow orchestrator.

        Args:
            max_parallel_agents: Maximum number of agents to run in parallel
            enable_progress_tracking: Enable progress tracking and logging
        """
        self.max_parallel_agents = max_parallel_agents
        self.enable_progress_tracking = enable_progress_tracking

        # Setup logging
        self.logger = self._setup_logger()

        # Track active workflows
        self.active_workflows: Dict[str, AgentContext] = {}

    def _setup_logger(self) -> logging.Logger:
        """
        Set up workflow logger.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger("workflow")
        logger.setLevel(logging.INFO)

        # Create logs directory
        log_dir = Path(".claude/logs/workflows")
        log_dir.mkdir(parents=True, exist_ok=True)

        # File handler
        log_file = log_dir / "workflow.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def create_context(
        self,
        task: str,
        **kwargs
    ) -> AgentContext:
        """
        Create a new workflow context.

        Args:
            task: Task description
            **kwargs: Additional context parameters

        Returns:
            AgentContext instance
        """
        context = AgentContext(task=task, **kwargs)
        self.active_workflows[context.workflow_id] = context
        self.logger.info(f"Created workflow context: {context.workflow_id}")
        return context

    def load_context(self, workflow_id: str) -> AgentContext:
        """
        Load existing workflow context.

        Args:
            workflow_id: Workflow ID to load

        Returns:
            AgentContext instance
        """
        # Check if already in active workflows
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]

        # Load from disk
        context = AgentContext.load(workflow_id)
        self.active_workflows[workflow_id] = context
        self.logger.info(f"Loaded workflow context: {workflow_id}")
        return context

    def run_sequential(
        self,
        agents: List[Tuple[str, BaseAgent]],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Run agents sequentially (one after another).

        Each agent receives the context updated by previous agents.
        Stops on first failure unless error handling is configured.

        Args:
            agents: List of (agent_name, agent_instance) tuples
            context: Shared workflow context

        Returns:
            Dictionary with workflow results:
            {
                "status": "completed" | "failed",
                "agents_run": ["agent1", "agent2", ...],
                "results": {agent_name: result, ...},
                "error": error_message (if failed)
            }

        Example:
            ```python
            result = workflow.run_sequential([
                ("database-expert", DatabaseExpert()),
                ("backend-developer", BackendDeveloper()),
                ("frontend-developer", FrontendDeveloper())
            ], context)
            ```
        """
        self.logger.info(f"Starting sequential workflow with {len(agents)} agents")

        results = {}
        agents_run = []

        try:
            for i, (agent_name, agent) in enumerate(agents):
                # Update context
                context.current_agent = agent_name
                context.phase = f"agent_{i+1}_of_{len(agents)}"

                # Progress tracking
                if self.enable_progress_tracking:
                    progress = (i + 1) / len(agents) * 100
                    self.logger.info(
                        f"[{progress:.0f}%] Running agent {i+1}/{len(agents)}: {agent_name}"
                    )

                # Run agent
                result = agent.run(context)
                results[agent_name] = result
                agents_run.append(agent_name)

                # Check if agent failed
                if result.get("status") == "failed":
                    self.logger.error(f"Agent '{agent_name}' failed")
                    return {
                        "status": "failed",
                        "agents_run": agents_run,
                        "results": results,
                        "error": f"Agent '{agent_name}' failed: {result.get('error')}"
                    }

            # All agents completed
            self.logger.info("Sequential workflow completed successfully")
            return {
                "status": "completed",
                "agents_run": agents_run,
                "results": results
            }

        except Exception as e:
            self.logger.error(f"Sequential workflow failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "agents_run": agents_run,
                "results": results,
                "error": str(e)
            }

        finally:
            # Save context
            context.save()

    def run_parallel(
        self,
        agents: List[Tuple[str, BaseAgent]],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Run agents in parallel (concurrently).

        All agents receive the same initial context. Use this when agents
        work on independent tasks that don't depend on each other.

        Args:
            agents: List of (agent_name, agent_instance) tuples
            context: Shared workflow context

        Returns:
            Dictionary with workflow results:
            {
                "status": "completed" | "partial" | "failed",
                "agents_completed": ["agent1", "agent2", ...],
                "agents_failed": ["agent3", ...],
                "results": {agent_name: result, ...}
            }

        Example:
            ```python
            # Build 3 microservices in parallel
            result = workflow.run_parallel([
                ("backend-service-1", BackendDeveloper()),
                ("backend-service-2", BackendDeveloper()),
                ("backend-service-3", BackendDeveloper())
            ], context)
            ```
        """
        self.logger.info(f"Starting parallel workflow with {len(agents)} agents")

        results = {}
        agents_completed = []
        agents_failed = []

        # Limit parallelism
        max_workers = min(self.max_parallel_agents, len(agents))

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all agents
                future_to_agent = {
                    executor.submit(agent.run, context): (agent_name, agent)
                    for agent_name, agent in agents
                }

                # Process completed agents
                for future in as_completed(future_to_agent):
                    agent_name, agent = future_to_agent[future]

                    try:
                        result = future.result()
                        results[agent_name] = result

                        if result.get("status") == "completed":
                            agents_completed.append(agent_name)
                            self.logger.info(f"Agent '{agent_name}' completed")
                        else:
                            agents_failed.append(agent_name)
                            self.logger.error(f"Agent '{agent_name}' failed")

                    except Exception as e:
                        agents_failed.append(agent_name)
                        results[agent_name] = {"status": "failed", "error": str(e)}
                        self.logger.error(f"Agent '{agent_name}' raised exception: {e}")

            # Determine overall status
            if not agents_failed:
                status = "completed"
            elif agents_completed:
                status = "partial"
            else:
                status = "failed"

            self.logger.info(
                f"Parallel workflow finished: {len(agents_completed)} completed, "
                f"{len(agents_failed)} failed"
            )

            return {
                "status": status,
                "agents_completed": agents_completed,
                "agents_failed": agents_failed,
                "results": results
            }

        except Exception as e:
            self.logger.error(f"Parallel workflow failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "agents_completed": agents_completed,
                "agents_failed": agents_failed,
                "results": results,
                "error": str(e)
            }

        finally:
            # Save context
            context.save()

    def run_conditional(
        self,
        agents: List[Tuple[str, BaseAgent, Optional[Callable[[AgentContext], bool]]]],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Run agents with conditional execution.

        Each agent can have an optional condition function that determines
        whether it should run based on the current context state.

        Args:
            agents: List of (agent_name, agent_instance, condition_func) tuples
                   condition_func: Optional function that takes context and returns bool
            context: Shared workflow context

        Returns:
            Dictionary with workflow results (same as run_sequential)

        Example:
            ```python
            def needs_migration(ctx):
                return ctx.get("database_changes", False)

            def needs_security_audit(ctx):
                return ctx.get("handles_authentication", False)

            result = workflow.run_conditional([
                ("backend-developer", backend_agent, None),  # Always runs
                ("database-expert", db_agent, needs_migration),  # Conditional
                ("security-auditor", security_agent, needs_security_audit),  # Conditional
                ("frontend-developer", frontend_agent, None)  # Always runs
            ], context)
            ```
        """
        self.logger.info(f"Starting conditional workflow with {len(agents)} agents")

        results = {}
        agents_run = []
        agents_skipped = []

        try:
            for i, (agent_name, agent, condition) in enumerate(agents):
                # Check condition
                should_run = True
                if condition is not None:
                    try:
                        should_run = condition(context)
                        self.logger.debug(
                            f"Condition for '{agent_name}': {should_run}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Condition function failed for '{agent_name}': {e}"
                        )
                        should_run = False

                if not should_run:
                    self.logger.info(f"Skipping agent '{agent_name}' (condition not met)")
                    agents_skipped.append(agent_name)
                    results[agent_name] = {"status": "skipped"}
                    continue

                # Update context
                context.current_agent = agent_name
                context.phase = f"agent_{i+1}_of_{len(agents)}"

                # Progress tracking
                if self.enable_progress_tracking:
                    progress = (i + 1) / len(agents) * 100
                    self.logger.info(
                        f"[{progress:.0f}%] Running agent {i+1}/{len(agents)}: {agent_name}"
                    )

                # Run agent
                result = agent.run(context)
                results[agent_name] = result
                agents_run.append(agent_name)

                # Check if agent failed
                if result.get("status") == "failed":
                    self.logger.error(f"Agent '{agent_name}' failed")
                    return {
                        "status": "failed",
                        "agents_run": agents_run,
                        "agents_skipped": agents_skipped,
                        "results": results,
                        "error": f"Agent '{agent_name}' failed: {result.get('error')}"
                    }

            # All agents completed
            self.logger.info(
                f"Conditional workflow completed: {len(agents_run)} run, "
                f"{len(agents_skipped)} skipped"
            )

            return {
                "status": "completed",
                "agents_run": agents_run,
                "agents_skipped": agents_skipped,
                "results": results
            }

        except Exception as e:
            self.logger.error(f"Conditional workflow failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "agents_run": agents_run,
                "agents_skipped": agents_skipped,
                "results": results,
                "error": str(e)
            }

        finally:
            # Save context
            context.save()

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Dictionary with workflow status
        """
        try:
            context = self.load_context(workflow_id)

            return {
                "workflow_id": workflow_id,
                "task": context.task,
                "phase": context.phase,
                "current_agent": context.current_agent,
                "agents_completed": context.agents_completed,
                "is_expired": context.is_expired(),
                "created_at": context.metadata.created_at,
                "updated_at": context.metadata.updated_at
            }

        except Exception as e:
            return {
                "workflow_id": workflow_id,
                "error": str(e)
            }

    def cancel_workflow(self, workflow_id: str):
        """
        Cancel an active workflow.

        Args:
            workflow_id: Workflow ID to cancel
        """
        if workflow_id in self.active_workflows:
            context = self.active_workflows[workflow_id]
            context.phase = "cancelled"
            context.save()
            del self.active_workflows[workflow_id]
            self.logger.info(f"Cancelled workflow: {workflow_id}")

    def archive_workflow(self, workflow_id: str):
        """
        Archive a completed workflow.

        Args:
            workflow_id: Workflow ID to archive
        """
        try:
            context = self.load_context(workflow_id)
            context.archive()

            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

            self.logger.info(f"Archived workflow: {workflow_id}")

        except Exception as e:
            self.logger.error(f"Failed to archive workflow {workflow_id}: {e}")

    def cleanup_expired_workflows(self):
        """Clean up all expired workflows"""
        self.logger.info("Cleaning up expired workflows")
        AgentContext.cleanup_expired()
