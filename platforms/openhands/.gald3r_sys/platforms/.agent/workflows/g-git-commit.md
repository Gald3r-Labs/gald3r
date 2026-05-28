Create a git commit: $ARGUMENTS

## What This Command Does

Creates a well-structured git commit integrated with the gald3r task management system.

## Git Commit Workflow

### 1. Gather Context
I'll analyze:
```powershell
git status                    # See all changes
git diff --staged            # See staged changes
git diff                     # See unstaged changes
git log -3 --oneline         # Recent commit style
```

And check gald3r context:
- Current in-progress tasks (from TASKS.md)
- Recently completed tasks
- Current phase
- Affected subsystems

### 2. Validation Check (for task-related commits)
Before committing task work:

```markdown
## 🔍 Pre-Commit Validation

### Compile/Import Check
- [ ] Code compiles without errors
- [ ] All imports resolve correctly
- [ ] No syntax errors

### Task Completion Check
- [ ] Task objective achieved
- [ ] Changes match task scope

**Validation**: [PASS/FAIL]
```

### 3. Stage Changes
I'll:
- Identify which files should be included
- Stage relevant files with `git add`
- **NEVER stage**: .env, credentials, secrets, API keys
- Confirm staged changes match intent

### 4. Generate Commit Message

**Task Commit Format:**
```
{type}({subsystems}): {task_title}

Task: #{task_id}
Phase: {phase}

{brief_summary_of_changes}
```

**Phase Commit Format:**
```
phase({N}): {Phase Name} complete

Tasks completed:
- #{id1}: {title1}
- #{id2}: {title2}

Subsystems: {affected_subsystems}
```

**General Commit Format:**
```
{type}: {brief_description}

{details}
```

### 5. Execute Commit
```powershell
git add {files}
git commit -m "$(cat <<'EOF'
{generated_message}
EOF
)"
```

### 6. Verify & Report
```powershell
git status                   # Confirm clean state
git log -1 --oneline        # Show commit hash
```

## Commit Type Reference

| Type | Task Type | Use Case |
|------|-----------|----------|
| `feat` | feature, task | New functionality |
| `fix` | bug_fix | Bug fixes |
| `refactor` | refactor | Code restructure |
| `docs` | documentation | Documentation |
| `test` | test | Test additions |
| `chore` | chore | Build/config changes |
| `phase` | - | Phase completion |

## Task Integration

**If task ID provided or detected:**
1. Read task file for metadata (subsystems, phase, type)
2. Include task reference in commit message
3. If task is complete, update status after commit
4. Sync TASKS.md

**Automatic Detection:**
- Check TASKS.md for `[🔄]` tasks
- Match changed files to task subsystems
- Suggest most likely related task

## Git Safety Rules

**NEVER:**
- ❌ Update git config
- ❌ Use `--force` push without permission
- ❌ Use `--no-verify` to skip hooks
- ❌ Commit secrets (.env, API keys, credentials)
- ❌ Use `--amend` on pushed commits

**ALWAYS:**
- ✅ Show what will be committed first
- ✅ Use conventional commit prefixes
- ✅ Reference related tasks when applicable
- ✅ Verify commit succeeded
- ✅ Run validation for task commits

## Usage Examples

**Basic:**
```
@g-git-commit
```
→ Analyzes changes, detects related task, generates message

**With task:**
```
@g-git-commit task 101
```
→ Commits work for task 101, uses task metadata

**With message:**
```
@g-git-commit "fix login bug"
```
→ Uses provided description, still detects task context

**Phase commit:**
```
@g-git-commit phase 1
```
→ Creates phase completion commit with all task references

## Semi-Automatic Behavior

By default, I will:
1. Generate the commit message
2. Show you the proposed commit
3. **Execute unless you say "skip"**

To skip: Say "skip", "no", or "don't commit"

Let's commit!
