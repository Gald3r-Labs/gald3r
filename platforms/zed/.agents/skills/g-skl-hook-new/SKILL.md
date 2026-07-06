---
subsystem_memberships: [PLATFORM_INTEGRATION]
skill_trust_level: core
---
# g-skl-hook-new - Create a new hook in your own project

Scaffolds a new automation hook **for your project** targeting an AI platform you choose. User-facing
counterpart to the maintainer-only `g-skl-gald3r-hook-new`. NEVER writes to `.gald3r_sys/`.

## Trigger Phrases
- `@g-hook-new <hook-name> <event>`
- "create a hook for my project", "automate on <event>"

## Operations

1. **Ask which platform(s)** to target - only those the project has installed
   (`.cursor/`, `.claude/`, etc.). Do not assume.
2. Collect: **hook-name**, **event** (a registered lifecycle event for the chosen platform, e.g.
   `sessionStart`, `beforeShellExecution`, `postToolUse`, `afterFileEdit`, `stop`).
3. Write `<platform>/hooks/<hook-name>.ps1` (or `.sh`) using the stdin-JSON contract:

```powershell
# <hook-name>.ps1 - <one-line description>
$inputJson = ""
if ([Console]::IsInputRedirected) { try { $inputJson = [Console]::In.ReadToEnd() } catch {} }
try {
    $event = if ($inputJson) { $inputJson | ConvertFrom-Json } else { @{} }
    # TODO: implement hook logic
    Write-Output '{"continue": true}'; exit 0     # exit 2 = block
} catch { Write-Output '{"continue": true}'; exit 0 }   # fail open
```

4. Write a companion `<hook-name>.md` (Fires On / What It Does / Side Effects).
5. Wire `<platform>/hooks.json` for `<event>` if it is a registered event.
6. Implement the body and test the JSON contract / exit codes.

## Related
- Command: `@g-hook-new`
- Maintainer-only (edits gald3r itself): `g-skl-gald3r-hook-new`
