---
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---
Activate the g-skl-compliance skill and run a SCAN operation: $ARGUMENTS

## What This Command Does

Runs a dependency/license scan against the current repository and writes a structured compliance
report to `.gald3r/reports/compliance_YYYYMMDD.md`.

## Scan Workflow

1. **Auto-detect scanner** — checks `$PATH` for: `ort` → `fossa` → `snyk` → `pmdc`/`pmd` → fallback
2. **Run scan** — executes the detected scanner against the current repo root
3. **Write report** — structured `.gald3r/reports/compliance_YYYYMMDD.md` with summary table and verdict
4. **Display verdict** — shows PASS / WARN / FAIL with actionable findings

## Options

| Option | Description |
|--------|-------------|
| `--scanner <name>` | Override auto-detection (ort\|fossa\|snyk\|pmd\|fallback) |
| `--path <dir>` | Scan a specific directory instead of cwd |

## Output

```
✅ COMPLIANCE: PASS    — all packages use permissive licenses
⚠️  COMPLIANCE: WARN    — weak copyleft or unknown licenses present
❌ COMPLIANCE: FAIL    — GPL/AGPL/proprietary restriction found
```

Report saved to: `.gald3r/reports/compliance_YYYY-MM-DD.md`

## What Happens After

- Run `@g-compliance-report` to display the last report
- Run `@g-compliance-gate` to get the exit-code verdict for hooks

## When to Use

- Before publishing or distributing your project
- After adding new dependencies
- In CI/CD pipelines via `@g-compliance-gate`
- Periodic audits of the dependency tree
