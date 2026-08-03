---
description: "Workspace-Control member .gald3r/ marker-only guard (HARD RULE) — a controlled_member or migration_source repository may carry ONLY .identity + PROJECT.md; live control-plane state (TASKS.md, BUGS.md, tasks/, bugs/, PLAN.md, FEATURES.md, SUBSYSTEMS.md, ...) is forbidden and must be blocked, not merely discouraged"
globs:
alwaysApply: true
subsystem_memberships: [WORKSPACE_COORDINATION]
---

# Workspace-Control Member `.gald3r/` Marker-Only Guard (HARD RULE) (g-rl-36)

> BUG-021 / T213 / T1435 (PROMOTE off-ramp) / T364 (this file — the rule was cited by four
> components before it existed; this closes that gap).

A repository registered in a workspace manifest (`.gald3r/linking/workspace_manifest.yaml`) with
`workspace_role: controlled_member` or `workspace_role: migration_source` is intentionally
restricted to a **slim, marker-only** `.gald3r/`. Its task/bug/plan state is owned by the
**controller** (the workspace's control project), not by the member repository itself. This rule
is the reason that ownership model is actually enforceable instead of aspirational.

## The Invariant

A `controlled_member` / `migration_source` repository's `.gald3r/` may contain **only**:

- `.gald3r/.identity`
- `.gald3r/PROJECT.md`

Everything else — most commonly `TASKS.md`, `BUGS.md`, `PLAN.md`, `FEATURES.md`,
`SUBSYSTEMS.md`, `tasks/`, `bugs/`, `config/`, `linking/`, `experiments/`, `logs/`, `reports/`,
`archive/`, `specifications_collection/`, `features/`, `releases/`, `subsystems/`, `prds/`,
`CONSTRAINTS.md`, `RELEASES.md`, `IDEA_BOARD.md`, `learned-facts.md` — is **live control-plane
state** and is forbidden in a member repository's `.gald3r/`, regardless of who or what is
writing it (human, agent, or a bare CLI verb).

**Exception**: an `installable_template` repository (`gald3r_template_slim`/`_full`/`_adv`) is
explicitly out of scope — its `.gald3r/` is *template content to be installed elsewhere*, not
live state, and the guard allows it (`template_directory_exception`).

## Enforcement Surfaces (defense in depth — no single layer is sufficient alone)

1. **PreToolUse hook** — `g-hk-pre-tool-call-member-gald3r-guard.py` intercepts Edit/Write tool
   calls and calls `gald3r workspace member guard --target-path PATH [--dot-gald3r-path REL]`
   (backed by `gald3r_core.project.workspace_member.guard.run_guard`). A target path resolving
   into a member's `.gald3r/` outside the marker allowlist is **denied** (exit 2). This hook
   catches agent Edit/Write tool calls — it does **not** catch a bare CLI invocation.
2. **CLI-level self-enforcement** — `scaffold_project()`
   (`gald3r_core.project.gald3r_integration.scaffold`) and its shape resolver
   (`project_type_shape.resolve_shape`) accept `is_controlled_member=True` and **filter out**
   every `MEMBER_DISALLOWED` path before ever touching the filesystem, regardless of the
   requested `--autonomy` level. This is required precisely because `gald3r setup` /
   `gald3r init` is a CLI verb, not an Edit/Write tool call, and therefore **bypasses the
   PreToolUse hook entirely** — the CLI path must refuse on its own (T364).
3. **`--workspace` flag** — `gald3r setup --workspace` (and `gald3r onboard`) tells the scaffold
   verb to treat the target as a Workspace-Control member and apply the same filtering as (2)
   even before a manifest lookup would otherwise resolve the role.

Do not treat any one of these as sufficient on its own: the hook does not see CLI writes, and the
CLI-level filter does not see agent Edit/Write calls to an already-scaffolded member's files. Both
must hold.

## The Off-Ramp: PROMOTE

A `controlled_member` is not permanently marker-only. `@g-wpac-promote <member-id> --apply` (backed
by `gald3r_core.coordination.workspace_member.promote`) flips `workspace_role` to
`autonomous_child` in both the member's `.identity` and the workspace manifest, after which this
guard's allowlist no longer applies to that repository. Following PROMOTE, `gald3r setup
--autonomy full` (idempotent — fills only what is missing, never overwrites) is the correct way to
top up a promoted member to the complete framework shape.

## Rationalization Table

| Rationalization | Reality |
|---|---|
| "It's just a status update, not a real task" | Any write outside the marker pair is control-plane state. Blocked. |
| "The CLI verb doesn't go through Edit/Write, so the guard doesn't apply" | Exactly why `scaffold_project()` self-enforces (T364) — the hook alone is not enough. |
| "The member repo already has TASKS.md from before" | Pre-existing violations are a BUG-021-class finding, not a precedent to extend. |
| "I'll write it once, just for now" | The guard has no time-boxed exception. Use the controller's `.gald3r/` for the real work. |
| "This member should really be autonomous" | Then PROMOTE it first (`@g-wpac-promote --apply`); don't write around the guard. |
