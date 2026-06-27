---
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---
# @g-git-push — Pre-push gate (regular vs release)

Run **`.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.py`** before `git push` to distinguish **routine** pushes from **release** pushes. Complements `@g-git-sanity` / `g-hk-pre-commit.py` and shared `.claude/skills/g-skl-git-commit/scripts/gald3r_git_sanity_common.py`.

---

## Modes

| Mode | How | Behavior |
|------|-----|----------|
| **regular** | Default (answer **N** at prompt, or no prompt in CI) | `git status`, unpushed commit summary, optional `.gald3r/` sync hint — **never blocks** |
| **release** | `-Release`, or `GALD3R_RELEASE_PUSH=1`, or answer **Y** at prompt | Requires a **versioned** `## [x.y.z]` section in `CHANGELOG.md` (not only `[Unreleased]`). Prints README/version file hints. **Blocks** exit 1 unless overridden |

---

## Usage (PowerShell)

```powershell
# Interactive — prompts "Is this a release push?"
./.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.py

# Explicit release checks
./.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.py -Release

# CI / non-interactive release
$env:GALD3R_RELEASE_PUSH = "1"
./.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.py -NonInteractive

# Agent wiring check (always exit 0)
./.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.py -DryRun
./.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.py -Release -DryRun
```

**Override** when release gate fails but you intend to push anyway:

```powershell
$env:GALD3R_PUSH_GATE_OVERRIDE = "1"
./.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.py -Release -NonInteractive
```

---

## Optional pre-push hook

Same opt-in hooks folder as pre-commit:

```powershell
git config core.hooksPath .cursor/hooks
```

Hook file: `.cursor/hooks/g-hk-pre-push.py`

- In **hook** mode, only **`GALD3R_RELEASE_PUSH=1`** selects release checks; otherwise the hook runs **regular** (informational, exit 0).

---

---

## Optional Compliance Gate (opt-in, disabled by default)

Before `git push`, an optional SCA (Software Composition Analysis) compliance check can be run to catch license violations before code reaches the remote.

**This gate is enabled by default.** The scanner auto-detects installed tools and skips gracefully if none are found. Disable in `.gald3r/config/COMPLIANCE_GATE.md`.

### Enabling the Gate

Set `enabled: true` in `.gald3r/config/COMPLIANCE_GATE.md`. When enabled, `.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.py` automatically adds `-ComplianceCheck` before the push proceeds.

### Gate Behavior

The compliance check runs `.claude/skills/g-skl-compliance/scripts/run_compliance_scan.py --gate-mode` and interprets exit codes:

| Exit Code | Meaning | Push Behavior |
|-----------|---------|---------------|
| 0 | PASS — no violations | Push proceeds |
| 1 | WARN — advisory issues | Advisory printed, push continues |
| 2 | FAIL — blocking violations | Push blocked with structured error |

### FAIL Block Message

When FAIL blocks a push, the message includes:
- Which scanner ran (ORT / FOSSA / Snyk / stub)
- Number of packages flagged FAIL
- Report file path for full detail
- Command to review: `@g-compliance-report`

Example:
```
❌ COMPLIANCE GATE BLOCKED
Scanner: ORT
Packages with FAIL-level violations: 3
Report: .gald3r/reports/compliance_scan_2026-05-09.json
Review with: @g-compliance-report

Violations must be resolved or explicitly approved before pushing.
Run @g-compliance-scan for details, or set GALD3R_PUSH_GATE_OVERRIDE=1 to override.
```

### Stub Detection

If `.claude/skills/g-skl-compliance/scripts/run_compliance_scan.py` is a stub (T906 not yet complete), the gate detects it and skips gracefully:
```
⚠️ Compliance scanner not yet configured — skipping gate.
   See @g-compliance-scan to set up.
```

### 30-Second Timeout

The compliance scan call has a 30-second timeout to prevent stalling CI pipelines.

---

## CI Gate (gald3r PR Review)

Every pull request automatically triggers the **gald3r CI review gate** via `.github/workflows/gald3r-review.yml`. The Claude Code GitHub Action runs `@g-go-review` on all changed files and posts a structured review comment on the PR.

- **Critical/High** findings → FAIL verdict, blocks merge
- **Medium/Low** findings → advisory comment, does not block

Requires `ANTHROPIC_API_KEY` stored as a GitHub Actions repository secret.

---

## Docs

- Skill: `g-skl-git-commit` (Pre-Push section)
- Rule: `g-rl-02-git_workflow` (push modes + release doc gate)
- Workflow: `.github/workflows/gald3r-review.yml`
