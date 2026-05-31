---
description: Capture session learning — write insights to .gald3r/learned-facts.md and optionally to the global vault memory note. No JSONL scanning. Safe for all session modes.
---
# /g-learn

Continual learning — file-only, no scanner risk.

## Usage

```
/g-learn                    → CAPTURE_SESSION (end-of-session summary, 3–5 facts)
/g-learn insight            → CAPTURE_INSIGHT (single fact, immediate)
/g-learn review             → REVIEW current facts (view + prune)
/g-learn global             → GLOBAL_SYNC selected facts to vault memory note
```

## Skill

Read and follow: `g-skl-learn`

## Memory files

- **Project**: `.gald3r/learned-facts.md`
- **Global**: `{vault_location}/projects/{project_name}/memory.md`
