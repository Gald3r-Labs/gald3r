---
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
# g-compress-memory

Compress the non-gald3r sections of memory files (`AGENTS.md`/`CLAUDE.md`/`*memory*.md`) to cut
token overhead, preserving gald3r-managed ranges. Activates **g-skl-compress-memory**.

## Usage
```
@g-compress-memory                 # SCAN (dry-run) AGENTS.md + CLAUDE.md
@g-compress-memory AGENTS.md       # scan a specific file
@g-compress-memory AGENTS.md --apply   # compress + apply (shows diff, asks confirmation first)
```

## What it does
1. **SCAN** (default, no writes): runs `gald3r_compress_memory.py` to report protected vs
   compressible token budgets and the ≥30% target.
2. **COMPRESS**: the agent rewrites only the compressible region (terse facts, drop redundant
   examples, dedup) — never the gald3r SECTION range, code blocks, or URLs.
3. **APPLY**: writes the new file only after showing a diff and getting explicit confirmation;
   the helper refuses unless the protected gald3r range is byte-identical.

In the gald3r **source** repo the whole memory file is gald3r-managed, so SCAN reports `skip`.

Helper: `.claude/skills/g-skl-compress-memory/scripts/gald3r_compress_memory.py`
