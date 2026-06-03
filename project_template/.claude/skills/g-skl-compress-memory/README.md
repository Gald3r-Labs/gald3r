---
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
# g-skl-compress-memory

Compress the **non-gald3r** parts of memory files (`AGENTS.md`, `CLAUDE.md`, vault `*memory*.md`)
to reduce per-session token overhead — while never touching the gald3r install-managed section,
code blocks, or URLs. The gald3r variant is marker-aware and **dry-run by default**.

## Quick start

```bash
# 1. See what's compressible (no writes)
pwsh -File scripts/gald3r_compress_memory.ps1            # scans AGENTS.md + CLAUDE.md
pwsh -File scripts/gald3r_compress_memory.ps1 -Path AGENTS.md -Json

# 2. (agent) rewrite the compressible region per SKILL.md, save a full new file

# 3. Apply — refuses unless the gald3r SECTION range is byte-identical
pwsh -File scripts/gald3r_compress_memory.ps1 -Path AGENTS.md -Apply -CompressedFile new.md -Confirm
```

## What it protects

| Always preserved | Compressible |
|---|---|
| `<!-- gald3r SECTION START -->`…`<!-- gald3r SECTION END -->` ranges | Project overview prose, custom notes |
| Fenced code blocks (verbatim) | Verbose multi-line learned facts → terse one-liners |
| URLs (verbatim) | Redundant examples / duplicate coverage / dup table rows |

## Behavior by context

- **gald3r source repo** (`.gald3r_sys/` present, no markers): `status=skip` — the whole file is
  gald3r-managed, nothing to compress.
- **Consumer project with markers**: compresses outside the markers; target ≥30% reduction.
- **Consumer project, no markers** (old install): `status=warn`; `-Force` to treat the whole file
  as user content.

## Safety

- Dry-run by default. `-Apply` needs `-Confirm` and refuses if protected ranges differ.
- Token estimates use a char/4 proxy (swap in `tiktoken` if exact counts are needed).

Command: `@g-compress-memory`. Skill spec: `SKILL.md`. Source task: T1053.
