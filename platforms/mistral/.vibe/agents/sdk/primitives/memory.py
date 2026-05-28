"""
Memory Integration for Agent SDK

Provides persistent storage and recall for agent decisions, preferences, and learnings.
Integrates with Cursor's .cursor/memory/ system.

Example:
    memory = Memory(agent_name="backend-developer")

    # Store a preference
    memory.store("database_preference", "PostgreSQL")

    # Recall a preference
    db = memory.recall("database_preference")

    # Search for related memories
    results = memory.search("authentication")

    # List all stored memories
    all_memories = memory.list_all()
"""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime


class Memory:
    """
    Cursor Memory integration for Agent SDK

    Provides agents with persistent storage for preferences, decisions, and learnings.
    Stores data in .cursor/memory/ for cross-session persistence.
    """

    def __init__(self, agent_name: str, memory_dir: str = ".cursor/memory"):
        """
        Initialize Memory integration

        Args:
            agent_name: Name of the agent (for namespacing)
            memory_dir: Base directory for memory storage
        """
        self.agent_name = agent_name
        self.memory_dir = Path(memory_dir)
        self.agent_memory_dir = self.memory_dir / "agent_decisions" / agent_name

        # Create directories
        self.agent_memory_dir.mkdir(parents=True, exist_ok=True)

        # Memory file
        self.memory_file = self.agent_memory_dir / "memory.json"

        # Load existing memories
        self.memories = self._load_memories()

    def store(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None):
        """
        Store a memory

        Args:
            key: Memory key (e.g., "database_preference")
            value: Memory value (can be any JSON-serializable type)
            metadata: Optional metadata (tags, source, etc.)

        Example:
            memory.store("database_preference", "PostgreSQL",
                        metadata={"source": "user_request", "confidence": 0.95})
        """
        memory_entry = {
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "timestamp": self._get_timestamp(),
            "agent": self.agent_name
        }

        # Store in memory dict
        self.memories[key] = memory_entry

        # Persist to disk
        self._save_memories()

    def recall(self, key: str, default: Any = None) -> Any:
        """
        Recall a memory by key

        Args:
            key: Memory key
            default: Default value if memory not found

        Returns:
            Memory value or default

        Example:
            db = memory.recall("database_preference", default="MySQL")
        """
        if key in self.memories:
            return self.memories[key]["value"]
        return default

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for memories matching a query

        Args:
            query: Search query (searches keys, values, and metadata)

        Returns:
            List of matching memory entries

        Example:
            results = memory.search("authentication")
            # Returns all memories related to authentication
        """
        query_lower = query.lower()
        matches = []

        for key, entry in self.memories.items():
            # Search in key
            if query_lower in key.lower():
                matches.append(entry)
                continue

            # Search in value (if string)
            if isinstance(entry["value"], str) and query_lower in entry["value"].lower():
                matches.append(entry)
                continue

            # Search in metadata
            metadata_str = json.dumps(entry["metadata"]).lower()
            if query_lower in metadata_str:
                matches.append(entry)

        return matches

    def list_all(self) -> Dict[str, Any]:
        """
        List all stored memories

        Returns:
            Dictionary of all memories

        Example:
            all_memories = memory.list_all()
            for key, entry in all_memories.items():
                print(f"{key}: {entry['value']}")
        """
        return self.memories.copy()

    def delete(self, key: str) -> bool:
        """
        Delete a memory

        Args:
            key: Memory key to delete

        Returns:
            True if deleted, False if not found
        """
        if key in self.memories:
            del self.memories[key]
            self._save_memories()
            return True
        return False

    def clear(self):
        """Clear all memories for this agent"""
        self.memories.clear()
        self._save_memories()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics

        Returns:
            Statistics about stored memories
        """
        return {
            "total_memories": len(self.memories),
            "agent": self.agent_name,
            "memory_file": str(self.memory_file),
            "oldest_memory": self._get_oldest_memory(),
            "newest_memory": self._get_newest_memory()
        }

    def _load_memories(self) -> Dict[str, Any]:
        """Load memories from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Memory] Error loading memories: {e}")
                return {}
        return {}

    def _save_memories(self):
        """Save memories to disk"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memories, f, indent=2)
        except Exception as e:
            print(f"[Memory] Error saving memories: {e}")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"

    def _get_oldest_memory(self) -> Optional[str]:
        """Get timestamp of oldest memory"""
        if not self.memories:
            return None
        oldest = min(self.memories.values(), key=lambda x: x["timestamp"])
        return oldest["timestamp"]

    def _get_newest_memory(self) -> Optional[str]:
        """Get timestamp of newest memory"""
        if not self.memories:
            return None
        newest = max(self.memories.values(), key=lambda x: x["timestamp"])
        return newest["timestamp"]


# Example usage
if __name__ == "__main__":
    # Create memory instance for backend developer
    memory = Memory(agent_name="backend-developer")

    # Store preferences
    memory.store("database_preference", "PostgreSQL",
                metadata={"source": "user_request", "confidence": 0.95})
    memory.store("test_framework", "pytest")
    memory.store("code_style", "black")

    # Recall a preference
    db = memory.recall("database_preference")
    print(f"Database preference: {db}")

    # Search for memories
    results = memory.search("test")
    print(f"Search results: {json.dumps(results, indent=2)}")

    # List all memories
    all_memories = memory.list_all()
    print(f"All memories: {json.dumps(all_memories, indent=2)}")

    # Get statistics
    stats = memory.get_stats()
    print(f"Memory stats: {json.dumps(stats, indent=2)}")
