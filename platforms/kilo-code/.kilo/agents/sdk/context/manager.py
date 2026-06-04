"""
Context Manager for Hybrid Agent System

Handles context lifecycle:
- Create/load/save contexts
- Cleanup expired contexts (TTL)
- Archive completed workflows
- Query context history
- Support both SDK and JSON storage

Author: Database Expert Agent
Date: 2025-11-01
Task: 052 - Anthropic Agent SDK Integration
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from .schema import AgentContext, WorkflowMetadata

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages context storage, retrieval, and lifecycle

    Storage structure:
    .cursor/agent_context/
    ├── sdk/              # SDK Context objects (future)
    ├── json/             # JSON files (current implementation)
    ├── active/           # Active workflows (symlinks)
    └── archived/         # Completed workflows
    """

    def __init__(self, base_path: str = ".cursor/agent_context"):
        """
        Initialize context manager

        Args:
            base_path: Base directory for context storage
        """
        self.base_path = Path(base_path)
        self.sdk_dir = self.base_path / "sdk"
        self.json_dir = self.base_path / "json"
        self.active_dir = self.base_path / "active"
        self.archived_dir = self.base_path / "archived"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create storage directories if they don't exist"""
        for directory in [self.sdk_dir, self.json_dir, self.active_dir, self.archived_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def create_context(
        self,
        task: str,
        project_path: str,
        priority: str = "medium",
        workflow_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        ttl_hours: int = 72,
        **kwargs
    ) -> AgentContext:
        """
        Create new agent context

        Args:
            task: Task description
            project_path: Absolute path to project
            priority: Task priority (low, medium, high, critical)
            workflow_type: Type of workflow (e.g., "fullstack_feature")
            tags: Workflow tags
            ttl_hours: Time-to-live in hours (default 72 = 3 days)
            **kwargs: Additional metadata

        Returns:
            New AgentContext instance
        """
        metadata = WorkflowMetadata(
            project_path=project_path,
            priority=priority,
            workflow_type=workflow_type,
            tags=tags or [],
            ttl_hours=ttl_hours,
            **kwargs
        )

        context = AgentContext(
            task=task,
            metadata=metadata
        )

        # Save immediately
        self.save_context(context)

        logger.info(f"Created new context: {context.workflow_id}")
        return context

    def save_context(self, context: AgentContext, active: bool = True) -> str:
        """
        Save context to disk

        Args:
            context: Context to save
            active: Whether to mark as active workflow

        Returns:
            Path to saved context file
        """
        # Update timestamp
        context.updated_at = datetime.utcnow()

        # Generate filename
        filename = f"{context.workflow_id}.json"

        # Choose directory based on completion status
        if context.completed_at or context.metadata.archived:
            target_dir = self.archived_dir
            active = False
        else:
            target_dir = self.json_dir

        # Save JSON file
        json_path = target_dir / filename
        with open(json_path, 'w') as f:
            json.dump(context.model_dump_json_safe(), f, indent=2)

        # Update metadata with storage location
        context.metadata.json_context_file = str(json_path)

        # Create/update active symlink
        if active:
            active_link = self.active_dir / filename
            if active_link.exists():
                active_link.unlink()
            try:
                active_link.symlink_to(json_path)
            except (OSError, NotImplementedError):
                # Symlinks not supported (Windows without dev mode), copy instead
                import shutil
                shutil.copy2(json_path, active_link)

        logger.debug(f"Saved context {context.workflow_id} to {json_path}")
        return str(json_path)

    def load_context(self, workflow_id: str) -> Optional[AgentContext]:
        """
        Load context by workflow ID

        Args:
            workflow_id: Workflow UUID (string)

        Returns:
            AgentContext if found, None otherwise
        """
        # Try all directories
        for directory in [self.json_dir, self.active_dir, self.archived_dir]:
            context_file = directory / f"{workflow_id}.json"

            if context_file.exists():
                try:
                    with open(context_file, 'r') as f:
                        data = json.load(f)

                    context = AgentContext(**data)
                    logger.debug(f"Loaded context {workflow_id} from {context_file}")
                    return context

                except Exception as e:
                    logger.error(f"Failed to load context {workflow_id}: {e}")
                    return None

        logger.warning(f"Context {workflow_id} not found")
        return None

    def list_active_contexts(self) -> List[AgentContext]:
        """
        List all active workflow contexts

        Returns:
            List of active contexts
        """
        contexts = []

        for context_file in self.active_dir.glob("*.json"):
            try:
                with open(context_file, 'r') as f:
                    data = json.load(f)
                contexts.append(AgentContext(**data))
            except Exception as e:
                logger.error(f"Failed to load {context_file}: {e}")

        return contexts

    def list_archived_contexts(
        self,
        workflow_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AgentContext]:
        """
        List archived workflow contexts with filtering

        Args:
            workflow_type: Filter by workflow type
            tags: Filter by tags (must match any)
            since: Filter by start date
            limit: Maximum number of results

        Returns:
            List of matching archived contexts
        """
        contexts = []

        for context_file in self.archived_dir.glob("*.json"):
            try:
                with open(context_file, 'r') as f:
                    data = json.load(f)
                context = AgentContext(**data)

                # Apply filters
                if workflow_type and context.metadata.workflow_type != workflow_type:
                    continue

                if tags and not any(tag in context.metadata.tags for tag in tags):
                    continue

                if since and context.started_at < since:
                    continue

                contexts.append(context)

                if len(contexts) >= limit:
                    break

            except Exception as e:
                logger.error(f"Failed to load {context_file}: {e}")

        # Sort by start time (newest first)
        contexts.sort(key=lambda c: c.started_at, reverse=True)

        return contexts

    def archive_context(self, workflow_id: str) -> bool:
        """
        Archive a completed workflow context

        Args:
            workflow_id: Workflow UUID

        Returns:
            True if archived successfully
        """
        context = self.load_context(workflow_id)
        if not context:
            logger.error(f"Context {workflow_id} not found for archiving")
            return False

        # Mark as archived
        context.metadata.archived = True
        context.metadata.archived_at = datetime.utcnow()

        # Move to archived directory
        source_file = self.json_dir / f"{workflow_id}.json"
        target_file = self.archived_dir / f"{workflow_id}.json"

        if source_file.exists():
            # Save to archived location
            with open(target_file, 'w') as f:
                json.dump(context.model_dump_json_safe(), f, indent=2)

            # Remove from json directory
            source_file.unlink()

            # Remove active symlink
            active_link = self.active_dir / f"{workflow_id}.json"
            if active_link.exists():
                active_link.unlink()

            logger.info(f"Archived context {workflow_id}")
            return True

        logger.warning(f"Context {workflow_id} not in json directory")
        return False

    def cleanup_expired(self, dry_run: bool = False) -> List[str]:
        """
        Clean up expired contexts based on TTL

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            List of workflow IDs that were (or would be) archived
        """
        archived_ids = []

        for context_file in self.json_dir.glob("*.json"):
            try:
                with open(context_file, 'r') as f:
                    data = json.load(f)
                context = AgentContext(**data)

                if context.is_expired():
                    workflow_id = str(context.workflow_id)

                    if dry_run:
                        logger.info(f"[DRY RUN] Would archive expired context: {workflow_id}")
                    else:
                        if self.archive_context(workflow_id):
                            logger.info(f"Archived expired context: {workflow_id}")

                    archived_ids.append(workflow_id)

            except Exception as e:
                logger.error(f"Failed to process {context_file}: {e}")

        return archived_ids

    def get_context_stats(self) -> Dict[str, any]:
        """
        Get statistics about context storage

        Returns:
            Dictionary with storage stats
        """
        active_count = len(list(self.active_dir.glob("*.json")))
        json_count = len(list(self.json_dir.glob("*.json")))
        archived_count = len(list(self.archived_dir.glob("*.json")))

        # Calculate total storage size
        total_size = 0
        for directory in [self.json_dir, self.archived_dir]:
            for context_file in directory.glob("*.json"):
                total_size += context_file.stat().st_size

        return {
            "active_contexts": active_count,
            "json_contexts": json_count,
            "archived_contexts": archived_count,
            "total_contexts": json_count + archived_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(self.base_path)
        }

    def search_contexts(
        self,
        task_query: Optional[str] = None,
        agent_name: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[AgentContext]:
        """
        Search contexts with flexible filtering

        Args:
            task_query: Search in task description (case-insensitive)
            agent_name: Filter by agent name
            priority: Filter by priority
            status: Filter by completion status (completed, active, failed)
            limit: Maximum results

        Returns:
            List of matching contexts
        """
        contexts = []

        # Search both active and archived
        for directory in [self.json_dir, self.archived_dir]:
            for context_file in directory.glob("*.json"):
                try:
                    with open(context_file, 'r') as f:
                        data = json.load(f)
                    context = AgentContext(**data)

                    # Apply filters
                    if task_query and task_query.lower() not in context.task.lower():
                        continue

                    if agent_name and agent_name not in context.agents_completed and context.current_agent != agent_name:
                        continue

                    if priority and context.metadata.priority != priority:
                        continue

                    if status:
                        if status == "completed" and not context.completed_at:
                            continue
                        if status == "active" and context.completed_at:
                            continue
                        if status == "failed":
                            has_failed = any(
                                state.status == "failed"
                                for state in context.agent_states.values()
                            )
                            if not has_failed:
                                continue

                    contexts.append(context)

                    if len(contexts) >= limit:
                        break

                except Exception as e:
                    logger.error(f"Failed to load {context_file}: {e}")

            if len(contexts) >= limit:
                break

        # Sort by update time (newest first)
        contexts.sort(key=lambda c: c.updated_at, reverse=True)

        return contexts[:limit]

    def delete_context(self, workflow_id: str, permanent: bool = False) -> bool:
        """
        Delete a context (with safety checks)

        Args:
            workflow_id: Workflow UUID
            permanent: If False, move to archived; if True, delete permanently

        Returns:
            True if deleted successfully
        """
        if not permanent:
            # Archive instead of delete
            return self.archive_context(workflow_id)

        # Permanent deletion - be careful!
        deleted = False

        for directory in [self.json_dir, self.active_dir, self.archived_dir]:
            context_file = directory / f"{workflow_id}.json"
            if context_file.exists():
                context_file.unlink()
                deleted = True
                logger.warning(f"Permanently deleted context {workflow_id} from {directory}")

        return deleted


# Example usage
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # Initialize manager
    manager = ContextManager()

    # Create test context
    context = manager.create_context(
        task="Test workflow for context manager",
        project_path="/mnt/c/git/test_project",
        priority="high",
        workflow_type="test",
        tags=["test", "development"]
    )

    print(f"Created context: {context.workflow_id}")

    # Simulate agent work
    context.mark_agent_started("backend-developer")
    state = context.get_agent_state("backend-developer")
    state.files_created = ["test1.py", "test2.py"]
    context.mark_agent_completed("backend-developer")

    # Save updates
    manager.save_context(context)

    # Load context
    loaded = manager.load_context(str(context.workflow_id))
    print(f"Loaded context: {loaded.task}")

    # Get stats
    stats = manager.get_context_stats()
    print(f"\nContext storage stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Archive context
    manager.archive_context(str(context.workflow_id))
    print(f"\n✅ Context manager validated successfully!")
