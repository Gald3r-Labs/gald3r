---
name: g-skl-plugins
maturity: beta
description: Authoritative reference for the gald3r plugin system — install, remove (uninstall), update, list, and per-project enable/disable git-cloned, SKILL.md-based third-party plugins via `gald3r plugin <verb>`. Documents the live `PluginManager` mechanism (git clone/pull/rmtree, GLOBAL install, no manifest, no ledger) plus the per-project ON/OFF association overlay (T287), and honestly flags the two operations (scaffold/NEW and CHECK_COMPAT) that are not implemented. Single source of truth for everything plugin-related.
token_budget: medium
subsystem_memberships: [PLUGIN_SYSTEM]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
