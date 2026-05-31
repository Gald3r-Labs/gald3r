---
description: Clean-room rewrite pipeline — harvest a repo, write all findings to IDEA_BOARD, create tasks for top candidates, and produce a gald3r-native implementation spec. Calls separate agents per phase.
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---
# g-crr (Clean-Room Rewrite)

Activates **g-skl-crr**. Full pipeline: deep harvest → mandatory IDEA_BOARD write → task triage → clean-room spec task.

> Each phase runs as an **independent background subagent**. The coordinator never implements — it routes, observes, and writes shared state between phases.

## Usage

```
@g-crr https://github.com/owner/repo
@g-crr https://github.com/owner/repo --target-subsystem 3d-pipeline
@g-crr https://github.com/owner/repo --ideas-only
@g-crr https://github.com/owner/repo --no-spec
@g-crr https://github.com/owner/repo --mode fast
@g-crr STATUS owner__repo
@g-crr RESUME owner__repo
```

## Phases

| Phase | Agent | Output |
|-------|-------|--------|
| 1 — Harvest | background subagent | vault note + 5-pass recon report |
| 2 — IDEA_BOARD | coordinator write | IDEA-HARVEST-NNN entries (mandatory, never skipped) |
| 3 — Task triage | background subagent | task files for immediate candidates |
| 4 — CRR spec | background subagent | master clean-room rewrite task (like T1187) |

## Flags

| Flag | Effect |
|------|--------|
| `--target-subsystem <name>` | Name of the gald3r subsystem the rewrite targets (read from SUBSYSTEMS.md) |
| `--ideas-only` | Stop after Phase 2 — no tasks, no spec |
| `--no-spec` | Run Phases 1–3, skip Phase 4 spec task |
| `--mode fast` | Route Phase 1/3/4 subagents to haiku-class models |
| `STATUS <slug>` | Show recon report status for a previously analyzed slug |
| `RESUME <slug>` | Resume from last completed phase (idempotent) |

## Clean Room Boundary

Capture/recon may observe and summarize source behavior, interfaces, workflows, data shapes, and architectural patterns. Generated gald3r artifacts MUST use original wording and local architecture terms — never copied source code, docs prose, prompts, tests, or unique strings. Keep source URL, license, and provenance in recon notes.

## See Also

- `@g-recon-repo` — Lightweight capture only
- `@g-res-deep` — Deep 5-pass analysis (Phase 1 of this pipeline)
- `@g-res-review` — Review existing recon reports
- `@g-res-apply` — Apply approved features to .gald3r/
