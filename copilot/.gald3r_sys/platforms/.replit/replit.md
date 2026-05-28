# gald3r Project Instructions (Replit Agent)

> Replit Agent auto-creates, auto-reads, and may self-update this file on every request.
> It is the PRIMARY instruction/memory surface for this Repl. Because the Agent can rewrite
> replit.md mid-session, re-prime these conventions at session start if they drift.
> Edit the canonical copy under .gald3r_sys/platforms/.replit/ — not the installed copy.
> AGENTS.md at the repl root is also honored and holds the full universal gald3r contract.

## Task Management
- This project uses gald3r for task management. All work is tracked in .gald3r/TASKS.md.
- Read the active task in .gald3r/tasks/task{id}_*.md before implementing.
- Reference the task ID in commits: feat(T{id}): description | fix(BUG-{id}): description.

## Architecture
- Read .gald3r/CONSTRAINTS.md before making architecture changes.
- Subsystem boundaries are documented in .gald3r/SUBSYSTEMS.md.

## Environment
- The Repl run/language/entrypoint config lives in .replit; the Nix toolchain in replit.nix.
- Those are environment config, not AI-instruction files — do not put conventions there.

## Bug Protocol
- Pre-existing bugs: document in .gald3r/BUGS.md — never silently ignore.

## Code Standards
- No bare TODO comments — use TODO[TASK-{id}->TASK-{new_id}] and file a follow-up task.
- Match the conventions already present in the file you are editing.
