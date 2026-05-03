# Code Reusability (DRY Enforcement)

## 3-Strike Rule
If logic appears **3+ times**, it MUST be extracted to a shared module. No exceptions.

## Before Writing New Code
1. Does a shared module already exist for this? → Use it
2. Can this be generalized for reuse? → Put it in `lib/` or `shared/`
3. Am I duplicating logic from another file? → Extract first

## Folder Conventions
| Category | Location |
|---|---|
| Utilities | `lib/utils/` or `src/lib/utils/` |
| Services | `lib/services/` or `src/lib/services/` |
| Types/DTOs | `lib/types/` or `src/lib/types/` |
| Config/Constants | `lib/config/` or `src/lib/config/` |
| Shared UI | `components/shared/` or `lib/components/` |
| Hooks | `lib/hooks/` or `src/lib/hooks/` |

Use barrel exports (`index.ts` / `__init__.py`) for clean imports.

## Anti-Patterns to Flag
- Copy-pasted logic across files → extract immediately
- Inline utility functions → move to `lib/utils/`
- Hardcoded values repeated → extract to `lib/config/constants`
- Fat classes/components mixing concerns → decompose
- Re-implementing stdlib functionality → use the standard library

## Self-Check (Every Response That Writes Code)
> Did I introduce duplicated code that should be a shared module?
> → If yes: extract to `lib/` or `shared/` before completing.
