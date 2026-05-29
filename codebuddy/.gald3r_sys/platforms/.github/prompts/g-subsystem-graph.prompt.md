Activate `g-skl-subsystem-graph` to generate or refresh `.gald3r/SUBSYSTEM_GRAPH.md`.

Reads all `.gald3r/subsystems/` files, maps dependency edges between subsystems, performs layer analysis (root/core/mid-tier/leaf/isolated), detects circular dependencies, and writes a Mermaid diagram with status tables to `.gald3r/SUBSYSTEM_GRAPH.md`.

Alias: `@g-dependency-graph --subsystems`

Use when:
- You want to see how subsystems depend on each other
- You've added or changed subsystem dependencies/dependents
- You want to identify root (no deps) vs leaf (nothing depends on them) subsystems
- You want to check for circular subsystem dependencies
