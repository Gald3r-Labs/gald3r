Activate `g-skl-dependency-graph` to generate or refresh dependency graphs for tasks and/or subsystems.

**Flags:**
- `@g-dependency-graph` — auto-detect from context (default: tasks)
- `@g-dependency-graph --tasks` — task graph only → `.gald3r/DEPENDENCY_GRAPH.md`
- `@g-dependency-graph --subsystems` — subsystem graph only → `.gald3r/SUBSYSTEM_GRAPH.md`
- `@g-dependency-graph --all` — both graphs in sequence

**Task graph** reads all `.gald3r/tasks/` files, builds the dependency graph, computes the critical path, identifies blockers and orphan tasks, and writes a Mermaid diagram to `.gald3r/DEPENDENCY_GRAPH.md`.

**Subsystem graph** reads all `.gald3r/subsystems/` files, maps dependency edges, performs layer analysis (root/core/mid-tier/leaf), detects cycles, and writes `.gald3r/SUBSYSTEM_GRAPH.md`.

Use when:
- You want to see what's blocking what (tasks)
- You want to understand subsystem dependency layers
- You've added or changed task or subsystem dependencies
- You want to know the critical path to completion
