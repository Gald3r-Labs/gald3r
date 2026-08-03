---
description: "Meaningful, specific naming — no generic single-word collisions (daemon/manager/handler/service/client). Fires whenever naming code symbols, files, folders, subsystems, or task/bug titles."
globs:
alwaysApply: true
subsystem_memberships: [BUG_AND_QUALITY]
---
# Meaningful, Specific Naming (No Generic Collisions) (g-rl-42)

**Fires whenever naming anything**: code symbols (classes, functions, modules),
files, folders, subsystems, services, config keys, or task/bug titles.

## The Rule

Give things **specific, descriptive names that a human can understand the
system from, without opening the file.** Generic single-word names
(`daemon`, `manager`, `handler`, `service`, `worker`, `client`, `server`,
`core`, `util`) are a violation whenever:

1. More than one thing in the codebase could plausibly be called that name, OR
2. The name describes *what kind of thing it is* rather than *what it does or owns*

If you genuinely need a short/simple alias for your own internal shorthand
(e.g. in conversation or a local variable), that's fine — but the **defined**
name (class, file, folder, subsystem) must still be meaningful. Attach the
short form with an underscore suffix/prefix if useful, never as the primary
name: `world_tree_daemon` is acceptable shorthand *reference*, but the actual
component must be named for what makes it distinct — e.g. `ValkyrieConnector`,
not `daemon`.

## Canonical Cautionary Example (real incident)

In `gald3r_core_dev`, the owner built the **Valkyrie** system — a Redis-backed
communication layer connecting a user's projects (and other users at the same
company working on the same projects). An agent named the implementation
just `daemon`. The codebase already had **multiple other daemons** doing
unrelated things. Once the naming collided, an agent got confused mid-task
and the owner could not help it sort out which "daemon" was which — the
ambiguity had already propagated through comments, logs, and its own
mental model. The fix cost far more than naming it `ValkyrieConnector` (or
similar) would have cost up front.

> **Still live:** the `.gald3r/daemon/` runtime folder and the
> `daemon_runtime` / `cmd_daemon_start` code paths are the unpaid remainder of
> that incident — a full `daemon → Valkyrie` rename (code + files + folder) is
> tracked as a dedicated task. Do not add new `daemon`-named surfaces.

## Before Naming Anything

1. **Search first**: does this name (or a close variant) already exist elsewhere
   in the codebase? If yes, and it refers to something else — do not reuse it.
2. **Name for what makes it distinct**, not its generic category:
   - `daemon` → `ValkyrieConnector` / `valkyrie_daemon`
   - `manager` → `TaskLifecycleManager`
   - `handler` → `InboundWebhookHandler`
   - `client` → `WorldTreeApiClient`
3. **Folders/subsystems**: name for the domain concept, not the file type
   (`valkyrie/` not `services/`, when there's a real domain name available).
4. **Runtime/state folders count too**: a folder that holds process bookkeeping
   (locks, state json) still deserves a domain name (`valkyrie/`), not a generic
   one (`daemon/`) — ambiguous folder names leak into gitignore rules, logs, and docs.
5. **If truly generic and there's no collision risk** (e.g. a single, obviously-scoped
   `utils.go` in a tiny package), a generic name is fine — this rule targets
   *ambiguity*, not brevity itself.

## Self-Check (every naming decision)

> "If I grep the whole codebase for this name, will I find something else
> that isn't this?" If yes — pick a more specific name now, not after the
> second collision.

| Rationalization | Reality |
|---|---|
| "It's obvious from context which daemon I mean" | It's obvious to you, right now. Not to the next agent, or you in 3 weeks. |
| "Renaming later is easy" | Renaming after the ambiguous name is in comments, logs, docs, and tasks is not easy — see the Valkyrie incident. |
| "Short names are faster to type" | Ambiguity debugging is slower than one extra word. |
| "This is just a temporary/internal name" | Temporary names ship permanently. Every. Single. Time. |
