---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
Activate `g-skl-subsystem-graph` to generate or refresh `.gald3r/SUBSYSTEM_GRAPH.md`.

Reads all `.gald3r/subsystems/` files, maps dependency edges between subsystems, performs layer analysis (root/core/mid-tier/leaf/isolated), detects circular dependencies, and writes a Mermaid diagram with status tables to `.gald3r/SUBSYSTEM_GRAPH.md`.

Alias: `@g-dependency-graph --subsystems`

Use when:
- You want to see how subsystems depend on each other
- You've added or changed subsystem dependencies/dependents
- You want to identify root (no deps) vs leaf (nothing depends on them) subsystems
- You want to check for circular subsystem dependencies

## L1 → L2 hierarchy view (T1458)

When subsystem spec files carry `parent_system:` (i.e. `PRODUCT_SYSTEMS.md` exists and tagging
has run), also render the **L1 product system → subsystem** containment hierarchy in Mermaid,
one edge per subsystem grouped under its `parent_system:`:

```
LOGGING_SYSTEM --> logging-hooks
LOGGING_SYSTEM --> claude-chat-logger
MEMORY_AND_KNOWLEDGE --> agent-memory
MEMORY_AND_KNOWLEDGE --> vault-knowledge-store
```

The flat dependency graph (above) is the **fallback** when no `parent_system:` data exists.
This containment view is orthogonal to `dependencies:` edges — it shows ownership grouping,
not runtime coupling.
