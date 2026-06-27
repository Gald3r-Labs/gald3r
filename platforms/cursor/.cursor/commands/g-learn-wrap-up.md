---
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
# g-learn-wrap-up

Manually flush session learning artifacts before ending a conversation — or any time you want to save without waiting for the automatic stop-event trigger.

## What It Does

1. **Chat log** — runs `g-hk-cursor-chat-logger.py` against the current session transcript
2. **Learned facts extraction** — runs `gald3r_nightly_learn.py` (force mode, bypasses the 5-stop counter)
3. **Vocab checkpoint** — confirms `.gald3r/vocab.md` is up to date
4. **Memory capture** — offers `memory_capture_session` summary via example_app MCP (optional, requires Docker)

## Usage

```
@g-learn-wrap-up
@g-learn-wrap-up --no-memory    # skip MCP memory capture (offline/fast)
@g-learn-wrap-up --chat-only    # only save the chat log
@g-learn-wrap-up --facts-only   # only run learned-facts extraction
```

## Related Commands (g-learn-* group)

| Command | Purpose |
|---|---|
| `@g-learn-wrap-up` | This command — manual session flush |
| `@g-learn-review` | Review and curate `.gald3r/learned-facts.md` |
| `@g-vocab-add` | Add abbreviation to `.gald3r/vocab.md` |
| `@g-vocab-list` | Show all active abbreviations |

## Implementation

Run these PowerShell steps in order:

```powershell
# 1. Chat log (resolve project root first)
$ProjectRoot = git -C . rev-parse --show-toplevel 2>$null
if (-not $ProjectRoot) { $ProjectRoot = (Get-Location).Path }

py "$ProjectRoot\.cursor\hooks\g-hk-cursor-chat-logger.py" `
   --project-path $ProjectRoot `
   --platform cursor `
   --status completed

# 2. Learned facts (force run, bypass counter)
py "$ProjectRoot\.gald3r_sys\skills\g-skl-learn\scripts\gald3r_nightly_learn.py" `
   -Force

# 3. Report vocab row count
$vocabFile = "$ProjectRoot\.gald3r\vocab.md"
if (Test-Path $vocabFile) {
    $rows = (Get-Content $vocabFile | Where-Object { $_ -match '^\|' -and $_ -notmatch '---' -and $_ -notmatch 'Abbreviation' }).Count
    Write-Host "📖 Vocab: $rows active abbreviations"
}
```

If `--no-memory` is NOT passed, also offer:

```
memory_capture_session(project_id=<from .gald3r/.identity>, summary=<session summary>)
```

## Notes

- The `g-learn-*` prefix groups all session-memory and knowledge commands together for visual discoverability (CRASH convention)
- This command is safe to run mid-session — it does not end the conversation
- The 5-stop counter in `g-hk-nightly-learn.py` is bypassed; the counter is NOT reset by this command
