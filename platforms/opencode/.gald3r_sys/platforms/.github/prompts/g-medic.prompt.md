
### PCAC Inbox Health Gate

Before medic mode detection, determine whether this project is a PCAC participant. PCAC is configured only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a PCAC group member.

If PCAC is configured, run the re-callable PCAC inbox check without `-BlockOnConflict` so L1 triage can still report health:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . }
```

If the output reports `INBOX CONFLICT GATE`, finish L1 triage and include a health severity/score impact, then stop before L2-L4 planning/apply work, task claiming, implementation, or verification. Require `@g-pcac-read` before continuing. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the medic summary. If PCAC is not configured, skip this gate and report `PCAC: not configured / skipped`.

Activate the **g-medic** skill.

Tiered .gald3r/ health and intervention system. Detects project state and runs appropriate level:

- L1 (default): Triage — structural integrity, file sync, health score, TTL resets. Auto-applies only when `--dry-run` is absent.
- L2: Diagnosis — plan coherence, dependency DAG, feature/task linkage. Generates MEDIC_REPORT_L2.md.
- L3: Surgery — cross-subsystem interface audit, capability gaps, constraint violations.
- L4: Ecosystem — Workspace-Control diagnostics plus optional PCAC linked-project checks.

Usage:
  @g-medic                      → L1 triage (safe default)
  @g-medic --level 2            → L1 + L2 (report only; add --apply to fix)
  @g-medic --level 3 --apply    → L1 + L2 + L3 (apply all fixes)
  @g-medic --ecosystem          → all 4 levels (Workspace-Control plus optional PCAC)
  @g-medic --dry-run            → report only at any level
  @g-medic --curate             → fragmentation dry-run with human-readable recommendations, `suggested_moves`, and `index_candidates` (default: writes gitignored reports under `.gald3r/reports/`; add `-NoReportFiles` on the script for stdout-only)
  @g-medic --curate --apply -ProposalJson <path> → applies only top-level `moves` after approval; backup + git mv + path patch FEATURES/SUBSYSTEMS/tasks + regen diagrams

Dry-run/output rules:
- `--dry-run` for L1-L4 is read-only: no status changes, no TTL resets, no identity/version writes, no backlog regeneration, no report files, and no member-repo changes.
- Active task orphan/phantom counts must parse both supported `TASKS.md` row formats before comparing against direct child `.gald3r/tasks/task*.md` files: bullet rows like `- [✅] **Task 090**: ...` and table rows like `| [📋] | [090](tasks/task090_*.md) | ... |`. Normalize Markdown links, optional `Task`/`T` prefixes, leading zeros, and subtask suffixes; dedupe by normalized task ID before counting. Archive, backup, imported, quarantine, and historical task folders are separate inventory, not active orphans.
- Material findings must be shown to the user in full. Do not hide high counts, ID lists, blocker categories, or skipped checks behind a short summary.

**Replaces**: @g-medic (now a deprecated alias for @g-medic)
