
### PCAC Inbox Health Gate

Before medic mode detection, run the re-callable PCAC inbox check without `-BlockOnConflict` so L1 triage can still report health:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . }
```

If the output reports `INBOX CONFLICT GATE`, finish L1 triage and include a health severity/score impact, then stop before L2-L4 planning/apply work, task claiming, implementation, or verification. Require `@g-pcac-read` before continuing. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the medic summary.

Activate the **g-medic** skill.

Tiered .gald3r/ health and intervention system. Detects project state and runs appropriate level:

- L1 (default): Triage — structural integrity, file sync, health score, TTL resets. Always auto-applies.
- L2: Diagnosis — plan coherence, dependency DAG, feature/task linkage. Generates MEDIC_REPORT_L2.md.
- L3: Surgery — cross-subsystem interface audit, capability gaps, constraint violations.
- L4: Ecosystem — linked project coordination (requires PCAC topology).

Usage:
  @g-medic                      → L1 triage (safe default)
  @g-medic --level 2            → L1 + L2 (report only; add --apply to fix)
  @g-medic --level 3 --apply    → L1 + L2 + L3 (apply all fixes)
  @g-medic --ecosystem          → all 4 levels (requires PCAC topology)
  @g-medic --dry-run            → report only at any level

**Replaces**: @g-medic (now a deprecated alias for @g-medic)
