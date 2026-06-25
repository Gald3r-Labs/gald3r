---
name: g-skl-compliance
tier: full
local_only: false
description: SCA/license compliance scanning — wraps ORT, FOSSA, Snyk, and PMD CPD behind a unified gald3r interface with SCAN/REPORT/GATE/STATUS operations. Produces structured compliance reports with pass/warn/fail verdicts.
triggers:
  - "@g-compliance-scan"
  - "@g-compliance-gate"
  - "@g-compliance-report"
  - "compliance scan"
  - "license check"
  - "dependency audit"
  - "SCA scan"
  - "is our code clean"
operations:
  - SCAN
  - REPORT
  - GATE
  - STATUS
token_budget: medium
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---

# g-skl-compliance

**Activate for**: `@g-compliance-scan`, `@g-compliance-gate`, `@g-compliance-report`, license compliance, dependency audit, SCA scan, "is our code clean?".

## Summary

Unified compliance skill wrapping ORT, FOSSA, Snyk, PMD CPD, and a file-first manifest fallback. Runs SCAN/REPORT/GATE/STATUS operations and writes structured `.gald3r/reports/compliance_YYYYMMDD.md` reports with PASS/WARN/FAIL verdicts. Zero external-tool dependency via manifest-parse fallback mode.

---

## Operations

### SCAN — Run compliance/license scan

```
Usage: @g-compliance-scan [--scanner <name>] [--path <repo-root>]
       Optional: --scanner ort|fossa|snyk|pmd|fallback  (bypass auto-detection)
```

**Step 1 — Auto-detect scanner** (first found wins):

```
Priority order:
1. ort       — ORT CLI (open source, preferred; requires Java)
2. fossa     — FOSSA CLI (requires FOSSA_API_KEY env var)
3. snyk      — Snyk CLI (requires `snyk auth`)
4. pmdc/pmd  — PMD CPD (clone detection only; no license scan)
5. fallback  — manifest-parse-only (zero external deps; reads package manifests)
```

Detection command (PowerShell):

```powershell
$scanner = $null
foreach ($cmd in @('ort','fossa','snyk','pmdc','pmd')) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $scanner = $cmd; break
    }
}
if (-not $scanner) { $scanner = 'fallback' }
```

**Step 2 — Run scan**

| Scanner | Command | Notes |
|---------|---------|-------|
| `ort` | `ort analyze -i . -o .gald3r/reports/ort_out` | Produces license + vuln report |
| `fossa` | `fossa analyze && fossa report attribution` | Requires `FOSSA_API_KEY` |
| `snyk` | `snyk test --json > .gald3r/reports/snyk_raw.json` | Requires prior `snyk auth` |
| `pmd`/`pmdc` | `pmdc cpd --minimum-tokens 50 --dir . --format xml` | Clone detection only; no license scan |
| `fallback` | Parse manifest files directly (see Fallback Mode below) | Offline; zero deps |

**Step 3 — Write report**

Report path: `.gald3r/reports/compliance_YYYYMMDD.md`

Report format:

```markdown
# Compliance Report — YYYY-MM-DD HH:MM UTC

**Scanner**: <name> <version>
**Repo root**: <absolute path>
**Verdict**: COMPLIANCE: PASS | WARN | FAIL

## Summary Table

| Package | Version | Declared License | Risk |
|---------|---------|-----------------|------|
| example-pkg | 1.2.3 | MIT | ok |
| copyleft-lib | 0.9.0 | GPL-3.0 | block |

## Findings

### BLOCK (must resolve before release)
- `copyleft-lib@0.9.0` — GPL-3.0 (copyleft — cannot distribute as proprietary)

### WARN (review before release)
- `some-lib@2.1.0` — LGPL-2.1 (weak copyleft — review linking model)

### OK
- N packages with permissive licenses
```

**Step 4 — Log to .gald3r/reports/**

```bash
# Invoke the scanner helper:
# TODO[TASK-906→TASK-<follow-up>]: Wire full ORT/FOSSA/Snyk/PMD pipeline
python .claude/skills/g-skl-compliance/scripts/run_compliance_scan.py -Scanner "$scanner" -RepoRoot "$(pwd)"
```

---

### REPORT — Display last scan results

```
Usage: @g-compliance-report
```

1. Find the most recent `.gald3r/reports/compliance_*.md` (sort by filename desc, take first).
2. If no report exists → print "No compliance report found. Run `@g-compliance-scan` first."
3. Print the full report content inline.
4. Surface the verdict line prominently:
   - `✅ COMPLIANCE: PASS` — all packages permissively licensed
   - `⚠️ COMPLIANCE: WARN` — review-only issues, no hard blockers
   - `❌ COMPLIANCE: FAIL` — hard blockers present (GPL/AGPL/unknown in proprietary context)

---

### GATE — Verdict for hooks (exit-code aware)

```
Usage: @g-compliance-gate
```

Reads the most recent report and returns a structured verdict:

| Verdict | Meaning | Hook exit code |
|---------|---------|---------------|
| `PASS` | No risks or only ok-tier licenses | 0 |
| `WARN` | LGPL/MPL/CDDL licenses present but no hard blockers | 1 |
| `FAIL` | GPL/AGPL/unknown licenses in a distribution context, or scan error | 2 |

When called from `.cursor/hooks/g-git-push` or `.claude/skills/g-skl-compliance/scripts/run_compliance_scan.py`:
- Exit 0 → allow push
- Exit 1 → warn but allow (unless `COMPLIANCE_GATE_STRICT=1` env var is set)
- Exit 2 → block push, print blocking packages

If no report exists: run SCAN first, then evaluate verdict.

---

### STATUS — Show available scanners

```
Usage: @g-compliance-status
```

Check which scanners are available on `$PATH` and report auth status:

```
Compliance Scanner Status
─────────────────────────
✅ ort       — found (v2.0.0)
❌ fossa     — not found  [install: https://github.com/fossas/fossa-cli]
❌ snyk      — not found  [install: npm install -g snyk]
❌ pmdc/pmd  — not found  [install: https://pmd.github.io]
✅ fallback  — always available (manifest-parse-only mode)

Active scanner: ort (priority 1)
FOSSA_API_KEY: not set
```

---

## Fallback Mode (manifest-parse-only)

When no external SCA tool is available, parse package manifests directly.

**Supported manifests**:

| File | Format | License field |
|------|--------|---------------|
| `package.json` | npm | `.license` |
| `requirements.txt` + `pyproject.toml` | Python | `[project].license` |
| `Cargo.toml` | Rust | `[package].license` |
| `go.mod` | Go | No standard field — flag as `unknown` |
| `pom.xml` | Java/Maven | `<licenses>` block |
| `*.gemspec` | Ruby | `.license` |

**License risk classification**:

| Risk tier | Licenses | Action |
|-----------|----------|--------|
| `block` | GPL-2.0, GPL-3.0, AGPL-3.0, SSPL | Cannot distribute as proprietary — must remediate |
| `warn` | LGPL-2.0, LGPL-2.1, LGPL-3.0, MPL-2.0, CDDL-1.0, EPL-2.0 | Weak copyleft — review linking model |
| `ok` | MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, 0BSD, Unlicense, CC0-1.0 | Permissive — no restrictions |
| `warn` | unknown / missing | No license declared — flag for review |

> Full license risk table: `.cursor/skills/g-skl-compliance/reference/license_risk_table.md`

**Fallback PASS/WARN/FAIL logic**:
- Any `block` license → `FAIL`
- Any `warn` license (including `unknown`) → `WARN`
- All `ok` → `PASS`

---

## Scanner Helper (Python)

`.claude/skills/g-skl-compliance/scripts/run_compliance_scan.py` — called by SCAN operation and `@g-compliance-gate` hook.

```bash
# TODO[TASK-906→TASK-<follow-up>]: Full ORT/FOSSA/Snyk/PMD pipeline implementation
# Phase-1 behavior: detect scanner name on PATH (ort/fossa/snyk/pmd/pmdc → fallback),
# write a placeholder report to .gald3r/reports/, print PASS diagnostics, and exit 0.
python .claude/skills/g-skl-compliance/scripts/run_compliance_scan.py -Scanner auto -RepoRoot "$(pwd)"

# Flags:
#   -Scanner / --scanner    auto | ort | fossa | snyk | pmd | pmdc | fallback (default: auto)
#   -RepoRoot / --repo-root  scan root (default: current directory)
#   -Strict  / --strict      gate mode — exit 2 on FAIL-level violations
```

---

## Report File Location

Reports are written to `.gald3r/reports/compliance_YYYYMMDD.md`.

Add to `.gald3r/.gitignore` (or project root `.gitignore`) if not already excluded:

```gitignore
.gald3r/reports/compliance_*.md
.gald3r/reports/ort_out/
.gald3r/reports/snyk_raw.json
```

---

## Integration Points

- **`@g-compliance-gate`** — used by `g-git-push` pre-push hook (T907) to block pushes with FAIL verdict
- **`@g-compliance-scan`** — can be triggered manually or from CI pipelines
- **`g-skl-res-review`** — harvest pipeline `similarity_risk` field (T908) complements license risk

---

## Scanner Setup Reference

> Full per-scanner install and auth instructions: `.cursor/skills/g-skl-compliance/reference/scanner_setup.md`

Quick install:

```bash
# ORT (preferred — open source)
# Requires Java 11+; download from https://github.com/oss-review-toolkit/ort/releases
brew install ort  # macOS
# Windows: download ort-*.zip and add to PATH

# FOSSA CLI
curl -H 'Cache-Control: no-cache' https://raw.githubusercontent.com/fossas/fossa-cli/master/install-latest.sh | bash
export FOSSA_API_KEY=<your-key>

# Snyk
npm install -g snyk
snyk auth

# PMD / PMD CPD
# Download from https://pmd.github.io/#downloads
# Add pmd/bin/ to PATH
```
