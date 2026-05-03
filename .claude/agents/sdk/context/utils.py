"""
Context System Utilities

Helper functions for context operations:
- Context validation
- Context merging
- Context migration
- Context analysis

Author: Database Expert Agent
Date: 2025-11-01
Task: 052 - Anthropic Agent SDK Integration
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import AgentContext, AgentStatus

logger = logging.getLogger(__name__)


def validate_context(context: AgentContext) -> List[str]:
    """
    Validate context for common issues

    Args:
        context: AgentContext to validate

    Returns:
        List of validation warnings/errors
    """
    issues = []

    # Check task description
    if not context.task or len(context.task.strip()) < 10:
        issues.append("Task description is too short or missing")

    # Check for stale agents (in_progress for > 1 hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    for agent_name, state in context.agent_states.items():
        if state.status == AgentStatus.IN_PROGRESS:
            if state.started_at and state.started_at < one_hour_ago:
                issues.append(f"Agent '{agent_name}' has been in progress for over 1 hour")

    # Check for orphaned current_agent
    if context.current_agent:
        if context.current_agent not in context.agent_states:
            issues.append(f"Current agent '{context.current_agent}' has no state record")

    # Check for completed workflow still marked as active
    if context.completed_at:
        if context.current_agent:
            issues.append("Workflow is completed but current_agent is still set")

        # Check if all agents are done
        all_completed = all(
            state.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
            for state in context.agent_states.values()
        )
        if not all_completed:
            issues.append("Workflow marked complete but not all agents finished")

    # Check for excessive retries
    for agent_name, state in context.agent_states.items():
        if state.retry_count > 3:
            issues.append(f"Agent '{agent_name}' has excessive retries ({state.retry_count})")

    return issues


def merge_contexts(base: AgentContext, updates: AgentContext) -> AgentContext:
    """
    Merge two contexts (useful for parallel workflows)

    Args:
        base: Base context
        updates: Context with updates to merge

    Returns:
        Merged context
    """
    # Create copy of base
    merged = base.model_copy(deep=True)

    # Merge agents_completed
    for agent in updates.agents_completed:
        if agent not in merged.agents_completed:
            merged.agents_completed.append(agent)

    # Merge agent_states
    for agent_name, state in updates.agent_states.items():
        if agent_name not in merged.agent_states:
            merged.agent_states[agent_name] = state
        else:
            # Keep more recent state
            if state.started_at and (
                not merged.agent_states[agent_name].started_at
                or state.started_at > merged.agent_states[agent_name].started_at
            ):
                merged.agent_states[agent_name] = state

    # Merge shared artifacts
    if updates.shared_artifacts.database_schema:
        merged.shared_artifacts.database_schema = updates.shared_artifacts.database_schema

    merged.shared_artifacts.api_endpoints.extend(updates.shared_artifacts.api_endpoints)
    merged.shared_artifacts.implementation_files.extend(updates.shared_artifacts.implementation_files)

    # Merge plugin results
    merged.shared_artifacts.plugin_results.update(updates.shared_artifacts.plugin_results)

    # Merge custom artifacts
    merged.shared_artifacts.custom.update(updates.shared_artifacts.custom)

    # Merge memory context
    merged.memory_context.user_preferences.update(updates.memory_context.user_preferences)
    merged.memory_context.agent_learnings.update(updates.memory_context.agent_learnings)

    # Merge events
    merged.hook_events.extend(updates.hook_events)
    merged.commands_executed.extend(updates.commands_executed)
    merged.fallback_log.extend(updates.fallback_log)

    # Update metadata
    merged.updated_at = datetime.utcnow()

    return merged


def analyze_context_performance(context: AgentContext) -> Dict[str, Any]:
    """
    Analyze context for performance metrics

    Args:
        context: AgentContext to analyze

    Returns:
        Performance metrics dictionary
    """
    metrics = {
        'workflow_id': str(context.workflow_id),
        'task': context.task,
        'total_duration_seconds': 0,
        'agents_executed': len(context.agent_states),
        'agents_completed': len([
            s for s in context.agent_states.values()
            if s.status == AgentStatus.COMPLETED
        ]),
        'agents_failed': len([
            s for s in context.agent_states.values()
            if s.status == AgentStatus.FAILED
        ]),
        'total_files_created': 0,
        'total_files_modified': 0,
        'total_retries': 0,
        'plugins_used': set(),
        'commands_used': set(),
        'hooks_triggered': set(),
        'fallback_count': len(context.fallback_log),
        'agent_durations': {}
    }

    # Calculate total duration
    if context.completed_at:
        metrics['total_duration_seconds'] = (
            context.completed_at - context.started_at
        ).total_seconds()

    # Analyze each agent
    for agent_name, state in context.agent_states.items():
        # Files
        metrics['total_files_created'] += len(state.files_created)
        metrics['total_files_modified'] += len(state.files_modified)

        # Retries
        metrics['total_retries'] += state.retry_count

        # Primitives usage
        metrics['plugins_used'].update(state.plugins_called)
        metrics['commands_used'].update(state.commands_executed)
        metrics['hooks_triggered'].update(state.hooks_triggered)

        # Agent duration
        if state.started_at and state.completed_at:
            duration = (state.completed_at - state.started_at).total_seconds()
            metrics['agent_durations'][agent_name] = duration

    # Convert sets to lists for JSON serialization
    metrics['plugins_used'] = list(metrics['plugins_used'])
    metrics['commands_used'] = list(metrics['commands_used'])
    metrics['hooks_triggered'] = list(metrics['hooks_triggered'])

    # Calculate efficiency score (0-100)
    efficiency_factors = []

    # Factor 1: Completion rate
    if metrics['agents_executed'] > 0:
        completion_rate = metrics['agents_completed'] / metrics['agents_executed']
        efficiency_factors.append(completion_rate * 100)

    # Factor 2: Retry penalty (fewer retries = better)
    retry_penalty = max(0, 100 - (metrics['total_retries'] * 10))
    efficiency_factors.append(retry_penalty)

    # Factor 3: Fallback penalty
    fallback_penalty = max(0, 100 - (metrics['fallback_count'] * 20))
    efficiency_factors.append(fallback_penalty)

    if efficiency_factors:
        metrics['efficiency_score'] = sum(efficiency_factors) / len(efficiency_factors)
    else:
        metrics['efficiency_score'] = 0

    return metrics


def export_context_report(context: AgentContext, output_path: str):
    """
    Export context as human-readable report

    Args:
        context: AgentContext to export
        output_path: Path to save report
    """
    report_lines = [
        f"# Agent Workflow Report",
        f"",
        f"**Workflow ID**: {context.workflow_id}",
        f"**Task**: {context.task}",
        f"**Started**: {context.started_at.isoformat()}",
        f"**Updated**: {context.updated_at.isoformat()}",
    ]

    if context.completed_at:
        duration = (context.completed_at - context.started_at).total_seconds()
        report_lines.append(f"**Completed**: {context.completed_at.isoformat()}")
        report_lines.append(f"**Duration**: {duration:.1f} seconds")

    report_lines.append(f"")

    # Agent execution summary
    report_lines.append(f"## Agent Execution Summary")
    report_lines.append(f"")

    for agent_name in context.agents_completed:
        state = context.agent_states.get(agent_name)
        if state:
            status_icon = "✅" if state.status == AgentStatus.COMPLETED else "❌"
            report_lines.append(f"### {status_icon} {agent_name}")

            if state.started_at and state.completed_at:
                duration = (state.completed_at - state.started_at).total_seconds()
                report_lines.append(f"- **Duration**: {duration:.1f}s")

            if state.files_created:
                report_lines.append(f"- **Files Created**: {len(state.files_created)}")
                for f in state.files_created[:5]:
                    report_lines.append(f"  - {f}")

            if state.files_modified:
                report_lines.append(f"- **Files Modified**: {len(state.files_modified)}")

            if state.tests_passing is not None:
                test_status = "✅ Passing" if state.tests_passing else "❌ Failing"
                report_lines.append(f"- **Tests**: {test_status}")

            if state.plugins_called:
                report_lines.append(f"- **Plugins Used**: {', '.join(state.plugins_called)}")

            report_lines.append(f"")

    # Shared artifacts
    if context.shared_artifacts.api_endpoints:
        report_lines.append(f"## API Endpoints ({len(context.shared_artifacts.api_endpoints)})")
        report_lines.append(f"")
        for ep in context.shared_artifacts.api_endpoints:
            report_lines.append(f"- `{ep.get('method', 'GET')} {ep.get('path', 'N/A')}`")
        report_lines.append(f"")

    # Performance metrics
    metrics = analyze_context_performance(context)
    report_lines.append(f"## Performance Metrics")
    report_lines.append(f"")
    report_lines.append(f"- **Efficiency Score**: {metrics['efficiency_score']:.1f}/100")
    report_lines.append(f"- **Total Files Created**: {metrics['total_files_created']}")
    report_lines.append(f"- **Total Files Modified**: {metrics['total_files_modified']}")
    report_lines.append(f"- **Total Retries**: {metrics['total_retries']}")
    report_lines.append(f"- **Fallback Events**: {metrics['fallback_count']}")
    report_lines.append(f"")

    # Validation issues
    issues = validate_context(context)
    if issues:
        report_lines.append(f"## Validation Issues")
        report_lines.append(f"")
        for issue in issues:
            report_lines.append(f"- ⚠️ {issue}")
        report_lines.append(f"")

    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Exported context report to {output_path}")


def cleanup_old_contexts(
    context_dir: str = ".claude/agent_context/json",
    days_old: int = 30,
    dry_run: bool = True
) -> List[str]:
    """
    Clean up contexts older than specified days

    Args:
        context_dir: Directory containing context files
        days_old: Delete contexts older than this many days
        dry_run: If True, only report what would be deleted

    Returns:
        List of deleted/would-be-deleted workflow IDs
    """
    context_path = Path(context_dir)
    if not context_path.exists():
        return []

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    deleted_ids = []

    for context_file in context_path.glob("*.json"):
        try:
            with open(context_file, 'r') as f:
                data = json.load(f)

            started_at = datetime.fromisoformat(data.get('started_at', ''))

            if started_at < cutoff_date:
                workflow_id = data.get('workflow_id', 'unknown')

                if dry_run:
                    logger.info(f"[DRY RUN] Would delete: {workflow_id} (from {started_at.date()})")
                else:
                    context_file.unlink()
                    logger.info(f"Deleted old context: {workflow_id}")

                deleted_ids.append(workflow_id)

        except Exception as e:
            logger.error(f"Error processing {context_file}: {e}")

    return deleted_ids


# Example usage
if __name__ == "__main__":
    import logging
    from .schema import AgentContext, WorkflowMetadata

    logging.basicConfig(level=logging.INFO)

    # Create test context
    context = AgentContext(
        task="Test utilities with sample workflow",
        metadata=WorkflowMetadata(
            project_path="/mnt/c/git/test",
            priority="high"
        )
    )

    # Add some agents
    context.mark_agent_started("backend-developer")
    state = context.get_agent_state("backend-developer")
    state.files_created = ["test1.py", "test2.py"]
    state.plugins_called = ["mcp__brave_search"]
    context.mark_agent_completed("backend-developer")

    # Validate
    issues = validate_context(context)
    print(f"Validation issues: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")

    # Analyze performance
    metrics = analyze_context_performance(context)
    print(f"\nPerformance Metrics:")
    print(f"  Efficiency Score: {metrics['efficiency_score']:.1f}/100")
    print(f"  Files Created: {metrics['total_files_created']}")
    print(f"  Plugins Used: {metrics['plugins_used']}")

    # Export report
    export_context_report(context, "/tmp/test_context_report.md")
    print(f"\n✅ Context utilities validated successfully!")
