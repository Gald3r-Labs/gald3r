---
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
# g-vocab-add

Add or update an abbreviation in `.gald3r/vocab.md`.

## Usage

```
@g-vocab-add "ABBR = Full expansion text — usage context"
@g-vocab-add "CRASH = Commands/Rules/Agents/Skills/Hooks — platform folder contents"
@g-vocab-add "CRASH = Commands/Rules/Agents/Skills/Hooks — platform folder contents" --local
```

## What It Does

1. Parses `ABBR = expansion — context` from the argument
2. Checks if the abbreviation already exists in local `vocab.md` (case-insensitive)
3. If new: appends a row to the `## Active Vocabulary` table
4. If exists: updates the existing row
5. **WPAC propagation** (unless `--local` flag): if `.gald3r/workspace/topology.md` exists and declares a resolvable local `parent:` path, also writes the entry to the parent's `.gald3r/vocab.md` — making it available workspace-wide
6. Confirms with: `📖 Added: ABBR → expansion [propagated to parent: {name}]` or `📖 Added: ABBR → expansion [local only]`

## Flags

- `--local` — write to this project only, skip WPAC propagation even if parent is reachable

## Behavior Rules

- Abbreviations are stored UPPERCASE by convention
- Context field is optional (defaults to "general")
- Agent loads the updated entry immediately for the rest of the session
- Duplicate check is case-insensitive and whole-word
- On collision between local and parent entries, local always wins at load time

## Vocab File Location

`.gald3r/vocab.md` — human-editable, always the source of truth for this project.
Parent vocab (read-only from this project's perspective unless `@g-vocab-add` propagates): `{parent_path}/.gald3r/vocab.md`
