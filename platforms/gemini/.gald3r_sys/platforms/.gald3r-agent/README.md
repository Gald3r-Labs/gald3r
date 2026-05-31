# gald3r_agent — gald3r Parity Scaffold

**Repo**: `G:/gald3r_ecosystem/gald3r_agent` (parity platform, not an install deploy target)

This directory documents the gald3r deploy model for **gald3r_agent**, the standalone agent
runtime. Unlike the IDE platforms here, gald3r_agent is **not** copied into end-user project
roots — it consumes the canonical `.gald3r_sys/` tree directly via symlink + reference copies.

Authoritative reference: project `CLAUDE.md` (Platform 7 — gald3r_agent, T1074) and
`custom_scripts/platform_parity_sync.ps1` (`-CheckAgent` / `-SyncAgent`).

> **Status (T1277 — documented):** see **`gald3r-agent_instructions.md`** in this directory.
> Because gald3r_agent is a parity platform with no installed-project output dir, there is no
> per-project config payload and no install `.gitignore` entry (T1277 AC6). It is intentionally
> NOT registered as an installable capability in `_platform_capabilities.json`.
