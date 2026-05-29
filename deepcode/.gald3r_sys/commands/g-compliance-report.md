---
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---
Activate the g-skl-compliance skill and run a REPORT operation: $ARGUMENTS

## What This Command Does

Displays the most recent compliance scan report from `.gald3r/reports/compliance_*.md`.

## What You'll See

The full compliance report including:
- **Scanner used** and version
- **Verdict**: PASS / WARN / FAIL
- **Summary table**: package | version | declared license | risk level
- **BLOCK findings** — packages that must be resolved before release
- **WARN findings** — packages that require review before release
- **OK packages** — count of packages with permissive licenses

## If No Report Exists

If no compliance report is found, this command will prompt you to run `@g-compliance-scan` first.

## Verdict Meanings

| Verdict | Meaning | Recommended action |
|---------|---------|-------------------|
| ✅ PASS | All permissive licenses | Safe to distribute |
| ⚠️ WARN | Weak copyleft or unknown licenses | Legal review recommended before release |
| ❌ FAIL | GPL/AGPL/strong copyleft found | Must remediate before proprietary distribution |

## Related Commands

- `@g-compliance-scan` — run a new scan
- `@g-compliance-gate` — machine-readable verdict for hooks
