# TASKS.md — {PROJECT_NAME}

**Project**: {project_name}
**Type**: {feature | maintenance | research}
**Plan**: `PLAN.md`
**Project overview**: `PROJECT.md`
**Constraints**: `CONSTRAINTS.md`
**Bugs**: `BUGS.md`
**Subsystems**: `SUBSYSTEMS.md`

---

## Status Indicators
<!-- DO NOT REMOVE THIS SECTION — agents depend on it for status parsing -->
- `[ ]` = Pending (no task file yet) — CODING BLOCKED
- `[📋]` = Task file created, ready to start
- `[📝]` = Spec being written (TTL: 1 hour)
- `[🔄]` = In Progress (claimed by agent, has TTL)
- `[🔍]` = Awaiting Verification (impl done, reviewer pending — different agent required)
- `[🕵️]` = Verification In Progress (claimed by verifier, has TTL; YAML: `verification-in-progress`)
- `[⏳]` = Resource-Gated (waiting on GPU/storage/API credits/external service)
- `[✅]` = Completed (verified by different agent)
- `[❌]` = Failed/Cancelled
- `[⏸️]` = Paused

---

## Task backlog (sequential IDs)

*Use sequential task IDs in `tasks/taskNNN_*.md`. Link PRDs from `PLAN.md`.*

### {Subsystem or category name}

*(No tasks yet — use `@g-task-new` to create the first task)*

---

## Bugs
*(See `BUGS.md` and individual files under `bugs/` for full detail.)*

---

## Completed Tasks
*(Tasks moved here when fully verified)*

---

**Last Updated**: {YYYY-MM-DD}
**Open Tasks**: 0
**Bugs**: 0 open
**Overall Progress**: 0 completed / 0 total
