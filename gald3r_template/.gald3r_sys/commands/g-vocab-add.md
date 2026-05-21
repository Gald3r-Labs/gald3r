# g-vocab-add

Add or update an abbreviation in `.gald3r/vocab.md`.

## Usage

```
@g-vocab-add "ABBR = Full expansion text — usage context"
@g-vocab-add "CRASH = Commands/Rules/Agents/Skills/Hooks — platform folder contents"
```

## What It Does

1. Parses `ABBR = expansion — context` from the argument
2. Checks if the abbreviation already exists in `vocab.md` (case-insensitive)
3. If new: appends a row to the `## Active Vocabulary` table
4. If exists: updates the existing row
5. Confirms with: `📖 Added: ABBR → expansion`

## Behavior Rules

- Abbreviations are stored UPPERCASE by convention
- Context field is optional (defaults to "general")
- Agent loads the updated entry immediately for the rest of the session
- Duplicate check is case-insensitive and whole-word

## Vocab File Location

`.gald3r/vocab.md` — human-editable, always the source of truth
