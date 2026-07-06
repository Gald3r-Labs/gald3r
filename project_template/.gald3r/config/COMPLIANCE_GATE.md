---
gald3r_rel_version: "3.0.0"
schema_version: "generic-v1"
---
# COMPLIANCE_GATE.md — SCA Pre-Push Gate Configuration

Controls whether `gald3r push-gate` runs a Software Composition Analysis (SCA) compliance check before allowing a `git push`.

---

## Configuration

```
enabled: true
```

**Default: enabled.** The gate detects stub/unconfigured scanners and skips gracefully — safe to leave on even before a real scanner is installed. Set `enabled: false` to disable entirely.

---

## What the Gate Does

When `enabled: true`, the push gate calls `.claude/skills/g-skl-compliance/scripts/run_compliance_scan.py --gate-mode` before any push proceeds.

| Scanner Exit Code | Meaning | Push Behavior |
|-------------------|---------|---------------|
| 0 | PASS | Push proceeds normally |
| 1 | WARN | Advisory printed; push continues |
| 2 | FAIL | Push blocked with structured error message |

A FAIL block includes: which scanner ran, how many packages are flagged, the report file path, and the command to review (`@g-compliance-report`).

---

## Prerequisites

This gate depends on T906 (`g-skl-compliance`). If `.claude/skills/g-skl-compliance/scripts/run_compliance_scan.py` is missing or is a stub, the gate detects this and skips gracefully with a warning rather than blocking the push.

---

## Override

To push despite a FAIL verdict (use sparingly, for emergency hotfixes):

```powershell
$env:GALD3R_PUSH_GATE_OVERRIDE = "1"
gald3r push-gate
```

Document the override reason in the commit message or PR description.

---

## Enabling for Your Project

1. Set `enabled: true` in this file
2. Ensure `.claude/skills/g-skl-compliance/scripts/run_compliance_scan.py` is configured (see `@g-compliance-scan`)
3. Test with `gald3r push-gate -DryRun` to verify gate behavior before first live push

---

## Related

- **T906** — `g-skl-compliance` skill and `run_compliance_scan.py`
- **T907** — this gate extension task
- **`@g-compliance-report`** — review full compliance scan results
- **`@g-compliance-scan`** — run compliance scan on demand
