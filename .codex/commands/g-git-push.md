# @g-git-push — Pre-push gate (regular vs release)

Run **`scripts/gald3r_push_gate.ps1`** before `git push` to distinguish **routine** pushes from **release** pushes. Complements `@g-git-sanity` / `g-hk-pre-commit.ps1` and shared `scripts/gald3r_git_sanity_common.ps1`.

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
./scripts/gald3r_push_gate.ps1

# Explicit release checks
./scripts/gald3r_push_gate.ps1 -Release

# CI / non-interactive release
$env:GALD3R_RELEASE_PUSH = "1"
./scripts/gald3r_push_gate.ps1 -NonInteractive

# Agent wiring check (always exit 0)
./scripts/gald3r_push_gate.ps1 -DryRun
./scripts/gald3r_push_gate.ps1 -Release -DryRun
```

**Override** when release gate fails but you intend to push anyway:

```powershell
$env:GALD3R_PUSH_GATE_OVERRIDE = "1"
./scripts/gald3r_push_gate.ps1 -Release -NonInteractive
```

---

## Optional pre-push hook

Same opt-in hooks folder as pre-commit:

```powershell
git config core.hooksPath .cursor/hooks
```

Hook file: `.cursor/hooks/g-hk-pre-push.ps1`

- In **hook** mode, only **`GALD3R_RELEASE_PUSH=1`** selects release checks; otherwise the hook runs **regular** (informational, exit 0).

---

## Docs

- Skill: `g-skl-git-commit` (Pre-Push section)
- Rule: `g-rl-02-git_workflow` (push modes + release doc gate)
