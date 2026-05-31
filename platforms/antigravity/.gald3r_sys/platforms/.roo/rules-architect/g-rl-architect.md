# gald3r Architect-Mode Rules (Roo Code)

> Modern directory form. Loaded in the built-in **Architect** mode (slug `architect`)
> for planning/design work. Roo reads `.roo/rules-architect/*.md` and places
> mode-specific rules BEFORE general rules in the system prompt. Edit the canonical
> copy under `.gald3r_sys/platforms/.roo/.roo/rules-architect/` — not the installed copy.

Always read `.gald3r/PLAN.md` and `.gald3r/CONSTRAINTS.md` before making architecture decisions.
Subsystem changes require reading the relevant `.gald3r/subsystems/{name}.md` spec first.
Record architectural decisions against the active task; do not blend conflicting patterns
(pick one, state why, flag the loser for cleanup).
