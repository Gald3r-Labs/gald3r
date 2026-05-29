# gald3r_agent Platform — gald3r Configuration Guide

**Platform**: gald3r_agent (the standalone gald3r agent runtime — 7th parity platform)
**Repo**: `G:/gald3r_ecosystem/gald3r_agent`
**gald3r Version**: 1.0.0
**Authoritative reference**: project `CLAUDE.md` (Platform 7 — gald3r_agent, T1074)

---

## This Is a Parity Platform, Not an Install Deploy Target

Unlike the IDE platforms in this directory (`.cursor/`, `.claude/`, `.aider/`, …), the
gald3r_agent is **not** deployed into end-user project roots by the installer. It is a
**parity platform**: a standalone agent runtime that lives at
`G:/gald3r_ecosystem/gald3r_agent` and consumes the canonical `.gald3r_sys/` tree directly.

This scaffold therefore documents the parity model; it does **not** ship a per-project
`.gald3r-agent/` IDE config folder (there is nothing to copy into a target project).

---

## How gald3r_agent Consumes the Canonical Tree

Per project `CLAUDE.md` (Platform 7, T1074) and `custom_scripts/platform_parity_sync.ps1`:

- gald3r_agent's `.gald3r_sys/` is a **symlink into the canonical tree**, so skills, agents,
  rules, hooks, and commands are **live-shared** — no copy step.
- The parity flow additionally maintains independent **reference copies** under the agent's
  own paths: `skills/`, `agents/`, `config/base_rules/`, `config/hooks_reference/`,
  `config/commands_reference/` (independent real copies — never junction/symlink).
- `-SyncAgent` also regenerates `config/base_system_prompt.md` (T1396).
- Agent-specific exclusions live under the `gald3r_agent:` section of
  `scripts/root_only_manifest.yaml`.

---

## Sync Operations (parity, not install)

```powershell
# Report-only parity check against gald3r_agent
custom_scripts/platform_parity_sync.ps1 -CheckAgent

# Apply parity sync to gald3r_agent (live symlink + reference copies + base prompt)
custom_scripts/platform_parity_sync.ps1 -SyncAgent
```

These are maintainer/parity operations — they are **not** part of the per-project
`setup_gald3r_project.ps1` install flow.

---

## gitignore Decision (T1277 AC6)

There is no installed-project `.gald3r-agent/` output directory, so there is **no install
`.gitignore` entry** for this platform. The gald3r_agent repo manages its own symlink and
reference-copy tracking per `root_only_manifest.yaml` — out of scope for installed projects.

---

## Common Pitfalls

- Do not treat gald3r_agent like an IDE deploy target — it consumes the canonical tree, it
  does not receive a copied config folder.
- Reference copies under the agent's own paths are **independent real copies** — never
  junction/symlink them (T1074 rule).
- Use `-CheckAgent` / `-SyncAgent`, not the per-project installer, to update gald3r_agent.
