---
subsystem_memberships: [BUG_AND_QUALITY]
---
# @g-doctor — Environment Health Check

Validate the complete gald3r environment: Docker MCP health, `.gald3r/` structure, vault configuration,
task sync state, and platform IDE targets. Outputs a structured pass/fail report with fix suggestions.

```
@g-doctor                # Full health report (read-only)
@g-doctor --fix          # Apply safe auto-fixes (narrow scope — see below)
@g-doctor identity       # Identity & Config checks only
@g-doctor tasks          # Task sync checks only
@g-doctor mcp            # MCP / Docker checks only
@g-doctor vault          # Vault checks only
@g-doctor platform       # Platform IDE parity checks only
```

**Fix scope is intentionally narrow** (the OpenClaw 5.5 lesson — their `doctor --fix` silently
rerouted API calls and broke user setups overnight):
- Creates missing `.gald3r/` subdirectories
- Writes a minimal `.gald3r/.identity` stub when the file is absent
- **NEVER** touches routing, credentials, connection types, or task state

---

## Execution Protocol

### Step 1: Run the PowerShell Script

```powershell
$scriptPath = @(
    ".gald3r_sys\skills\g-skl-medic\scripts\gald3r_doctor.ps1",
    ".cursor\skills\g-skl-medic\scripts\gald3r_doctor.ps1",
    ".claude\skills\g-skl-medic\scripts\gald3r_doctor.ps1"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($scriptPath) {
    $fixFlag  = if ($args -contains '--fix') { '-Fix' } else { '' }
    $catArg   = $args | Where-Object { $_ -in @('identity','tasks','mcp','vault','platform') } | Select-Object -First 1
    $catFlag  = if ($catArg) { "-Category $catArg" } else { '' }
    powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath $fixFlag $catFlag
} else {
    Write-Host "⚠️ g-skl-medic/scripts/gald3r_doctor.ps1 not found — running AI-assisted checks below."
}
```

If the script is present, display its output and stop. Exit code 1 = at least one FAIL.

### Step 2: AI-Assisted Checks (fallback when script is absent)

If the script could not be located, perform the following checks manually:

---

## Check Categories

### 1. Identity & Config

**AC3 — `.gald3r/.identity` validation**

Read `.gald3r/.identity` (key=value format, no quotes). Verify these fields are present and non-empty:
- `project_id` — stable UUID, set by `gald3r_install`
- `gald3r_version` — installed framework version
- `vault_location` — path or `{LOCAL}`

```
✅ PASS  identity/.identity fields  — project_id, gald3r_version, vault_location all present
❌ FAIL  identity/.identity fields  — Missing: project_id, gald3r_version
         💡 Edit .gald3r/.identity and add the missing fields
```

**`.gald3r/` structure check**

Verify presence of: `TASKS.md`, `PLAN.md`, `PROJECT.md`, `CONSTRAINTS.md`, `BUGS.md`, `SUBSYSTEMS.md`
and subdirectories: `tasks/`, `bugs/`, `subsystems/`

Missing files → `⚠️ WARN` (not FAIL — partial setups are valid during onboarding).

---

### 2. Task State

**AC5 — Task sync: TASKS.md ↔ tasks/ directory**

Parse task IDs from `TASKS.md` using both row formats:
- Table rows: `| [status] | [NNN](tasks/taskNNN_*.md) |`
- Bullet rows: `- [status] **Task NNN**:`

Compare against `tasks/task*.md` filenames.

```
⚠️ WARN  tasks/phantom  — 2 phantom task(s) in TASKS.md with no task file: 45, 112
         💡 Create missing task files or remove stale TASKS.md rows
⚠️ WARN  tasks/orphan   — 1 orphan task file(s) not in TASKS.md: 88
         💡 Add missing rows to TASKS.md or archive stale files
```

Phantom tasks and orphan files are `⚠️ WARN` (not `❌ FAIL`) unless count > 10.

---

### 3. MCP / Docker

**AC2 — Docker MCP server health**

1. Run `docker info` — PASS if exit 0, WARN if docker not found, FAIL if exit non-zero.
2. Run `docker ps --filter name=gald3r` — PASS if a container matches.
3. HTTP GET `http://localhost:8092/health` with 5s timeout:
   - 200 → `✅ PASS`
   - Non-200 → `⚠️ WARN` with status code
   - Unreachable → `⚠️ WARN` (WARN not FAIL — Docker is optional for file-first projects)
4. Check `node`, `python`, `uv` availability via `--version`.

---

### 4. Vault

**AC4 — Vault path validation**

Read `vault_location=` from `.gald3r/.identity`:
- `{LOCAL}` → look for `vault/` relative to project root; check for `_index.yaml`
- Absolute path → `Test-Path` the directory; check for `_index.yaml`
- HTTP/HTTPS URL → **AC7**: attempt `Invoke-WebRequest` with 8s timeout

```
✅ PASS  vault/location    — vault_location={LOCAL} (local vault mode)
⚠️ WARN  vault/index       — vault/_index.yaml missing
         💡 Run @g-vault-lint to regenerate the index
❌ FAIL  vault/directory   — Vault directory not found: <vault_path>
         💡 Update vault_location in .gald3r/.identity or create the directory
```

---

### 5. Platform IDE Parity

**AC6 — Platform targets check**

Verify directory presence for: `.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`, `.copilot/`

For `.cursor/` and `.claude/` (primary surfaces), also verify `commands/` and `skills/` subdirectories
and report file counts.

Missing platforms → `⚠️ WARN` with fix suggestion (not `❌ FAIL`).

---

### 6. Skills Quality (T1172 / T1259)

**Missing `token_budget:` declaration**

Scan all canonical SKILL.md files under `.claude/skills/` and `.gald3r_sys/skill_packs/`,
plus the IDE mirrors `.cursor/skills/`, `.claude/skills/`, `.codex/skills/`,
`.opencode/skills/`, `.agent/skills/`. For each SKILL.md, read the YAML frontmatter
and check for the `token_budget:` field.

```
⚠️ WARN  skills/token_budget  — N skill(s) missing token_budget: declaration
         💡 Add `token_budget: low|medium|high|very_high` to each skill's frontmatter.
            See .gald3r_sys/skill_packs/user-skills/skl-skill-create/SKILL.md
            §"token_budget: declaration (T1172)" for the band guide.
```

This is a **low-severity finding** (`⚠️ WARN`, never `❌ FAIL`). Skills without
`token_budget:` still work — the field is advisory metadata for `g-go`
coordinators and budget-aware swarm dispatch. The finding surfaces the gap so
authors can declare it during their next pass.

**Missing `skill_trust_level:` declaration** (parallel finding, T1056)

Same scan; check for the `skill_trust_level:` field. Same severity (`⚠️ WARN`).

```
⚠️ WARN  skills/skill_trust_level  — N skill(s) missing skill_trust_level: declaration
         💡 Add `skill_trust_level: core|community|local` to each skill's frontmatter.
            See .gald3r_sys/skill_packs/user-skills/skl-skill-create/SKILL.md
            §"skill_trust_level: declaration (T1056)" for the values.
```

**Reporting**: list the first 10 offending skill names; if more, append `... and N more`.
Group the two findings under a `## Skills Quality` heading in the report body when any
skill is missing either field.

---

## Output Format

**AC8 — Structured report**

```
gald3r doctor — Environment Health Report
==================================================

✅ PASS  identity/.identity fields     — project_id, gald3r_version, vault_location all present
⚠️ WARN  mcp/health-endpoint          — MCP server not reachable at http://localhost:8092/health
         💡 Run: cd docker && docker compose up -d
❌ FAIL  vault/directory               — Vault directory not found: <shared_vault>
         💡 Update vault_location in .gald3r/.identity or create the directory

==================================================
Summary: ✅ 12 PASS  ⚠️  1 WARN  ❌ 1 FAIL
```

- One line per check: `[status]  [check name]  — [detail]`
- Fix hint on the next line, indented, prefixed with `💡`
- Summary line at the end
- Exit code: `0` = all PASS/WARN, `1` = any FAIL

---

## When to Use

- Before starting a new gald3r session to verify environment is healthy
- After installing or upgrading gald3r in a project
- When MCP tools behave unexpectedly
- As part of a CI preflight check (script exits 1 on any FAIL)
- When onboarding a new project member

## Related Commands

- `@g-setup` — Initialize or repair a gald3r project
- `@g-medic` — Deep `.gald3r/` structural health and intervention
- `@g-status` — Project task/bug/phase status overview
- `@g-vault-lint` — Vault integrity check and index regeneration
