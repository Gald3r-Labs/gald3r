---
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---
Activate the g-skl-compliance skill and run a GATE operation: $ARGUMENTS

## What This Command Does

Returns a machine-readable compliance verdict suitable for pre-push hooks and CI/CD pipelines.
Reads the most recent `.gald3r/reports/compliance_*.md` report.

## Exit Codes

| Code | Verdict | Meaning |
|------|---------|---------|
| 0 | PASS | No compliance issues — all licenses are permissive |
| 1 | WARN | Weak copyleft or unknown licenses — warn but allow by default |
| 2 | FAIL | GPL/AGPL/strong copyleft or scan error — block by default |

## Behavior

- If no report exists: runs `SCAN` first, then evaluates verdict
- If `COMPLIANCE_GATE_STRICT=1` env var is set: exit 1 (WARN) also blocks
- Prints blocking packages to stderr on FAIL

## Hook Integration (T907)

This command is consumed by `@g-git-push` pre-push compliance check:

```powershell
# In .cursor/hooks/g-pre-push.ps1
python .gald3r_sys/scripts/run_compliance_scan.py -Scanner auto
if ($LASTEXITCODE -eq 2) {
    Write-Error "COMPLIANCE FAIL — push blocked. Run @g-compliance-report for details."
    exit 1
}
```

## Strict Mode

```powershell
$env:COMPLIANCE_GATE_STRICT = "1"
# Now WARN also blocks the push
```

## Related Commands

- `@g-compliance-scan` — run a fresh scan
- `@g-compliance-report` — display full report with findings
