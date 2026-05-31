---

## Purpose

Close the "detect and forget" loop. When a non-code defect is discovered (spec_defect, policy_incongruity, design_gap), this skill:

1. **ASSESSes** risk — computes a numeric score; high risk = do not touch
2. **FIXes** bounded, safe issues automatically (score ≤ threshold)
3. **LOGs** every attempt to the audit trail regardless of outcome

**The goal is not to be brave. The goal is to leave fewer things silently broken.**

subsystem_memberships: [BUG_AND_QUALITY, AGENT_ORCHESTRATION]
--- risk — computes a numeric score; high risk = do not touch
2. **FIXes** bounded, safe issues automatically (score ≤ threshold)
3. **LOGs** every attempt to the audit trail regardless of outcome

**The goal is not to be brave. The goal is to leave fewer things silently broken.**

---

## Operations

### ASSESS

Compute risk score without writing anything.

```
ASSESS bug_id=BUG-098 kind=spec_defect files=["workspace_manifest.yaml"]
```

Returns:
```yaml
risk_score: 1.5
eligible: true
reason: "spec_defect + single schema file + comment-only fix"
```

### FIX

Attempt a bounded auto-fix. Only runs if `risk_score ≤ auto_triage_risk_threshold` (default: 2.0).

```
FIX bug_id=BUG-098 kind=spec_defect fix_type=schema_comment
```

Fix types available in Phase 1:
- `schema_comment` — append clarifying comment to a YAML schema value
- `manifest_annotation` — add NOTE: inline to workspace_manifest.yaml
- `command_annotation` — add `BUG[BUG-NNN]` comment at bug site in a command file
- `rule_annotation` — add `BUG[BUG-NNN]` comment at bug site in a rule file
- `constraint_expire` — mark a constraint `status: archived` when expiry conditions are clearly met

### LOG

Write an audit entry regardless of outcome. Called internally by FIX but can be called standalone.

```
LOG bug_id=BUG-098 outcome=auto_resolved risk_score=1.5 note="Added clarifying comment"
```

Appends to: `.gald3r/logs/triage_auto_YYYYMMDD.log`

---

## Risk Score Reference

```
risk_score = base_kind_score + file_sensitivity_bonus + scope_multiplier
```

### Base kind scores

| kind | base_score | Notes |
|---|---|---|
| `code` | ∞ | NEVER auto-triage — code bugs go to normal fix path |
| `spec_defect` | 1.0 | Safe starting point |
| `policy_incongruity` | 2.0 | Borderline — only simplest fixes |
| `design_gap` | 3.0 | Always needs_attention — human decision required |

### File sensitivity bonus (added to base)

| File type | Bonus |
|---|---|
| Schema YAML comment | +0.0 |
| Manifest annotation | +0.5 |
| Rule file (`.mdc`) | +1.0 |
| Command file | +1.0 |
| `AGENT_CONFIG.md` | +1.0 |
| `CONSTRAINTS.md` body | +∞ (block) |
| `TASKS.md`, `tasks/` | +∞ (block) |
| `BUGS.md`, `bugs/` | +∞ (block) |
| `workspace/` topology | +∞ (block) |
| Any source code file | +∞ (block) |

### Scope multiplier

| Files affected | Multiplier |
|---|---|
| 1 file | ×1.0 |
| 2–3 files | ×1.5 |
| >3 files | ×∞ (block) |

**Threshold (Phase 1): `risk_score ≤ 2.0` → attempt fix.**

---

## Outcome States

| `triage_status` | Meaning | Bug badge |
|---|---|---|
| `auto_resolved` | Fix applied cleanly | ✅ |
| `needs_attention` | Human required (risk too high or fix failed) | 🚨 |
| `blocked_by_risk` | Score exceeded threshold — logged, no write made | ⛔ |
| `deferred_verify` | Fix applied, human should confirm before closing | 🔍 |
| `not_attempted` | Triage not yet run for this bug | — |

---

## Bug Frontmatter Fields (added by this skill)

```yaml
kind: spec_defect          # code | spec_defect | design_gap | policy_incongruity
triage_status: auto_resolved   # not_attempted | auto_resolved | needs_attention | blocked_by_risk | deferred_verify
triage_risk_score: 1.5
triage_attempted: '2026-05-21T11:55:00Z'
triage_notes: 'Added clarifying comment to workspace_manifest.yaml line 1205'
```

---

## Phase 1 Hard Limits (DO NOT EXCEED)

1. **Never touch** `TASKS.md`, `tasks/`, `BUGS.md`, `bugs/` — coordination state is sacred
2. **Never touch** `CONSTRAINTS.md` body text
3. **Never touch** `workspace/` topology files
4. **Never touch** source code in member repos
5. **Never fix** anything requiring a design decision (`design_gap`)
6. **Never fix** more than 3 files in a single triage run
7. **Always write** to audit log — even if no fix was attempted
8. **Always verify** the file was written cleanly after a write

---

## Invocation (via scripts)

```powershell
# Assess only
.\scripts\calculate_risk.ps1 -Kind "spec_defect" -Files @("workspace_manifest.yaml") -FixType "schema_comment"

# Full triage (assess + fix if safe + log)
.\scripts\invoke_triage.ps1 -BugId "BUG-098" -Kind "spec_defect" -Files @("G:\gald3r_ecosystem\gald3r_dev\.gald3r\linking\workspace_manifest.yaml") -FixType "schema_comment" -ProjectRoot "G:\gald3r_ecosystem\gald3r_dev"
```

---

## Audit Log Format

```
2026-05-21T11:55:00Z | BUG-098 | spec_defect | risk=1.5 | auto_resolved | Added clarifying comment to workspace_manifest.yaml
2026-05-21T11:56:00Z | BUG-099 | policy_incongruity | risk=3.5 | blocked_by_risk | Score exceeds threshold 2.0
```

---

## Phase 2 Expansion (future — not implemented)

- Higher threshold option (`auto_triage_risk_threshold: 3.5`)
- `design_gap` human-prompt mode (surfaces a proposed resolution, waits for approval)
- Integration with `g-go-code` as a pre-step impact classifier
- Cross-platform parity sync after spec_defect auto-resolve
