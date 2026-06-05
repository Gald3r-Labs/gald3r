---
name: g-skl-compress-memory
description: Compress the NON-gald3r sections of AGENTS.md/CLAUDE.md (and *memory*.md) to cut token overhead, while strictly preserving the install-managed gald3r SECTION ranges, code blocks, and URLs. Dry-run by default; apply only after confirmation.
token_budget: low
skill_trust_level: core
allowed-tools: [Read, Edit, Bash]
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
# g-skl-compress-memory

Memory files (`AGENTS.md`, `CLAUDE.md`, vault `*memory*.md`) grow unboundedly as learned facts,
project notes, and custom content accumulate — burning context tokens every session. This skill
compresses the **compressible** (non-gald3r) regions while treating the gald3r install-managed
section as **off-limits**.

## Hard constraint — never touch protected ranges
Content between `<!-- gald3r SECTION START -->` and `<!-- gald3r SECTION END -->` is managed by
`gald3r_install` / `gald3r_update`. It MUST NOT be compressed, rewritten, reordered, or touched.
The apply path refuses to write unless the protected ranges are **byte-identical** to the original.

> **Source-repo note:** in the gald3r *source* repo (`<gald3r_source>` — `.gald3r_sys/` present, no
> markers in the file) the **entire** memory file is gald3r-managed, so the skill **skips** it.
> Compression applies in *consumer* projects where `gald3r_install` injected a marked section.

## When to Use
- `AGENTS.md`/`CLAUDE.md` learned-facts / custom sections have grown verbose (1000+ lines).
- You want to cut session token overhead without losing technical accuracy.

## Operations

### SCAN (default, dry-run — never writes)
```bash
pwsh -File .claude/skills/g-skl-compress-memory/scripts/gald3r_compress_memory.ps1
# or a specific file: -Path AGENTS.md   ; machine-readable: -Json
```
Reports per file: `status` (`compressible` | `skip` | `warn`), total / protected / compressible
token estimates (char/4 proxy), and the ≥30% reduction target on the compressible region.
`status=skip` ⇒ source repo / fully gald3r-managed (nothing to do). `status=warn` ⇒ a consumer
file with no markers (old install) — re-run with `-Force` to treat the whole file as user content.

### COMPRESS (the agent's job — LLM rewrite of the compressible region only)
Apply these techniques to the compressible region **only**; never the protected range:
1. **Learned facts**: collapse multi-line prose facts into single-line entries that keep the
   technical value (dates, file paths, numbers, command names).
2. **Redundant examples**: drop inline examples when the rule is clear without them.
3. **Duplicate coverage**: when two facts say the same thing, keep the more specific one.
4. **Table dedup**: remove rows whose information is stated elsewhere.
5. **Code blocks**: never shorten or rewrite — copy verbatim.
6. **URLs**: never alter.
Produce a **full new file** with the protected gald3r range left byte-identical.

### APPLY (writes — requires confirmation)
```bash
pwsh -File .../gald3r_compress_memory.ps1 -Path AGENTS.md -Apply -CompressedFile new_full.md -Confirm
```
The helper re-detects the gald3r ranges in both files and **refuses to write** unless they match
byte-for-byte. No `-Confirm` ⇒ no write. Always show the user a diff + the dry-run token delta first.

## Workflow (safe sequence)
1. **SCAN** → get compressible token budget + confirm `status=compressible`.
2. Read the file; **COMPRESS** the compressible region per the techniques above → write the full
   new file to a temp path (protected range untouched).
3. Show the user the diff and projected token reduction; on confirmation, **APPLY**.
4. Re-run SCAN to record the achieved reduction.

## Boundaries
- Dry-run by default; modifies tracked files only via `-Apply -Confirm`.
- Never compresses gald3r SECTION ranges, code blocks, or URLs.
- Not a parity operation — it edits a project's own memory files, not the framework corpus.
