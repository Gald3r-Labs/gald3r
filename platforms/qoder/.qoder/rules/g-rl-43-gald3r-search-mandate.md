---
description: Prefer the gald3r search CLI verb for codebase content search; mandatory whenever a search must see .gald3r/ or .gald3r_sys/
globs:
alwaysApply: true
subsystem_memberships: [AGENT_ORCHESTRATION]
---

# gald3r search Mandate (g-rl-43)

> BUG-519: the g-go/g-go-code/g-go-review coordinator loop never invoked `gald3r search`
> (T257, `src/gald3r_core/cli/commands/search_cmd.py`) despite it already existing and
> already being gitignore-agnostic. Nothing instructed agents to prefer it, so the tool
> sat unused while every session fell back to raw bash `grep` or the harness/ripgrep-backed
> `Grep` tool instead.

## The Rule

For **codebase content search**, prefer `gald3r search <pattern> [--path DIR] [--glob PATTERN]`
over raw bash `grep`/`find` or the harness `Grep` tool.

`gald3r search` is **MANDATORY, not just preferred**, whenever a search must see inside
`.gald3r/` or `.gald3r_sys/` (or any other gitignored tree you need real results from). Do
not substitute `Grep` or bash `grep` for those searches under any circumstance.

## Why This Is Not Optional for Gitignored Trees

- The harness `Grep` tool is ripgrep-backed and **respects `.gitignore`** on broad/recursive
  searches. A bare recursive `Grep` from the repo root **silently skips gitignored
  directories** — no error, no warning, just missing results.
- `.gald3r_sys/` is gitignored (`git check-ignore .gald3r_sys` exits `0`) and holds real
  `.py` files that a broad ripgrep search will not see. A coordinator searching for a symbol
  that lives only under `.gald3r_sys/` gets a **false negative** and may wrongly conclude the
  symbol or file does not exist.
- Raw bash `grep -rn` is accidentally gitignore-safe (plain `grep` has no `.gitignore`
  concept) but is noisy and slow — it walks `.venv`, `node_modules`, `__pycache__`, etc. and
  needs manual filtering.
- `gald3r search` was purpose-built (T257) to give **both** properties at once:
  gitignore-agnostic (it inherits `grep_handler`'s behavior, which only skips the same
  fixed housekeeping dirs `.git`, `__pycache__`, `node_modules`, `gald3r_venv`, `.venv`,
  `dist`, `build`, `.pytest_cache` — never anything from `.gitignore`) **and**
  auto-excludes those housekeeping dirs, so it needs no manual noise filtering either.

## `.gald3rignore` Is the Only Exclusion Source (T560)

The gitignore-agnostic behavior above used to be an implementation ACCIDENT — nothing
in `grep_handler` was ever tested or documented to guarantee it, so a future change
could silently start reading `.gitignore` and reintroduce the exact false-negative
class this rule exists to prevent. T560 closes that gap:

- `gald3r search` / `grep_handler` **NEVER** read `.gitignore`, `.git/info/exclude`, or
  any other VCS ignore mechanism, full stop — this is now a tested contract
  (`tests/tools/handlers/test_gald3rignore.py`, `tests/cli/test_search_cmd.py`), not an
  incidental side effect.
- The **only** user-controlled search exclusion source is an optional `.gald3rignore`
  file at the repository root (`src/gald3r_core/tools/handlers/gald3rignore.py`). One
  glob pattern per line, `#` starts a comment, blank lines skipped. Pattern syntax
  deliberately mirrors `--glob`/`file_pattern` (BUG-624)'s existing basename-vs-relative-
  path split: a pattern with no `/` (e.g. `secrets.txt`, `*.key`) matches at any depth;
  a pattern containing `/` (e.g. `docs/drafts/*.md`) is matched relative to the repo
  root. Naming a directory excludes everything beneath it.
- A file excluded by `.gald3rignore` is reported separately from a genuinely-absent
  pattern via `output["gald3rignore_excluded_files"]` (distinct from `candidate_files`,
  same "don't silently conflate two different zero-counts" discipline BUG-624
  established for `--glob`).

## Repro (confirms the false-negative)

```bash
git check-ignore .gald3r_sys                       # exit 0 -- ignored
rg <symbol>                                          # bare, from repo root -- misses .gald3r_sys/
gald3r search <symbol> --path .gald3r_sys            # finds it
```

## When Each Tool Is Appropriate

| Situation | Use |
|---|---|
| Searching `.gald3r/` or `.gald3r_sys/` content (tasks, bugs, subsystem specs, compiled IP, any gitignored tree) | `gald3r search` — **mandatory** |
| General codebase content search (source, docs, config) with no gitignored-tree dependency | `gald3r search` — preferred |
| Interactive IDE search where a human is visually scanning results and gitignore-blindness is an acceptable/expected trade-off | `Grep` tool is fine |
| File-name/path search (not content) | `Glob` / `gald3r_core.tools.handlers.glob` — unaffected, this rule is about content search only |

## Rationalization Table

| Rationalization | Reality |
|---|---|
| "Grep is faster to reach for, it's already in my tool list" | Fast and wrong beats slow and right in no scenario. Grep silently omits `.gald3r_sys/` results. |
| "I searched and found nothing, so it doesn't exist" | You may have searched a gitignore-aware tool against a gitignored tree. Re-run with `gald3r search` before concluding absence. |
| "bash grep works fine, no gitignore issue there" | True, but it's slow/noisy and still not the sanctioned path — use `gald3r search` so behavior is consistent and documented. |
| "This search doesn't touch .gald3r/ or .gald3r_sys/, so Grep is safe here" | Then Grep is acceptable per the table above — but confirm that before assuming it, not after a false negative. |
| "Nobody told me gald3r search existed" | This rule, `GUARDRAILS.md`, and the g-go/g-go-code/g-go-review command prompts all now point at it. |
| "I'll just add the exclusion to .gitignore, it's the same idea" | `.gitignore` is never consulted by `gald3r search` — add it to `.gald3rignore` instead, or it will keep showing up in results. |
