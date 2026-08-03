---
name: g-skl-valk
description: Drive the resident Valkyrie world_tree connector (`gald3r valk`) directly — live peer-to-peer ask/inquire, connector status, durable events ledger, and world_tree base-URL/login setup. Complements g-skl-wpac-* file-transport skills.
token_budget: low
subsystem_memberships: [WORKSPACE_COORDINATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

> **Multi-agent framework:** direct live coordination via the resident Valkyrie
> connector, as opposed to the git-committed WPAC file transport (`g-skl-wpac-*`).
# g-skl-valk

## When to Use Valkyrie vs WPAC File-Transport

Both share the same cross-project coordination goal; they differ in transport:

| | **Valkyrie** (`gald3r valk`, this skill) | **WPAC file-transport** (`g-skl-wpac-*`) |
|---|---|---|
| Medium | Live HTTP calls to world_tree (`POST /api/v1/ask`, `/ask/stream`) via the resident connector | Committed markdown: `.gald3r/workspace/inbox.md`, `sent_orders/*.md` |
| Latency | Near-real-time (seconds) | Asynchronous — actioned at the peer's next session |
| Requires | world_tree reachable + authed (`gald3r login`) | Nothing — works fully offline / air-gapped |
| Audit trail | Durable events ledger (`.gald3r/valkyrie/messages/<date>.jsonl`, read via `valk messages`) | Git history of the markdown files themselves |
| Failure mode | Fails soft to file transport (`ask`/`inquire` are write-ahead queued, T250) | N/A — is itself the fallback |

**In practice these are not either/or.** As of WPAC-v2 (T1608/T1609), `g-skl-wpac-ask`'s own
Step 0 already tries the live transport first (`gald3r workspace outbox send --verb ask`) and
only falls back to the file steps when world_tree is `offline`/`error`/`auth_required`. Reach
for **this skill** (`g-skl-valk`) specifically when you want to:

- Ask a **direct, immediate** grounded question to another project without creating a WPAC
  request/task record (`valk ask` / `valk inquire`)
- Check whether **this repo's** resident connector is up and pointed at the right API
  (`valk status`)
- Read the **durable events ledger** of everything the connector has received
  (`valk messages`) — notifications, inbound asks, inquiries
- Diagnose or fix **connectivity/auth/base-URL** problems before falling back to file transport

## World_Tree Base-URL Resolution (ground truth — read from source, not assumed)

Resolution precedence, implemented once and shared by every `gald3r workspace`/`valk` verb
(`src/gald3r_core/server_bridge/workspace/wpac_client.py:376-391`, `resolve_base_url()`):

1. **`WORLD_TREE_URL`** env var (WPAC convention) — wins if set
2. **`GALD3R_WORLD_TREE_URL`** env var (agent/Throne `gald3r login` convention) — checked next
3. The **stored token's `base_url`** — whatever host `gald3r login` last wrote (OS keyring
   service `gald3r-world-tree`, or the 0600 `world_tree_token.json` fallback under the unified
   per-user home; see `wpac_client.py:428-455`, `load_stored_token()`)
4. **`DEFAULT_BASE_URL`** — the hardcoded fallback when none of the above are set

> **T343 (owner ruling 2026-07-21) — the default IS the production host.** `DEFAULT_BASE_URL`
> is `https://api.gald3r.ai` (`src/gald3r_core/server_bridge/wpac_claim/http.py`, re-exported
> by `wpac_client.py`) — a repo with **no** `WORLD_TREE_URL`/`GALD3R_WORLD_TREE_URL` set and
> **no** stored login token resolves to the real, JWT-gated API and **fails closed (401)**
> until `gald3r login`. This supersedes BUG-238/T329: the old `http://localhost:8082` dev
> fallback (and the one-time localhost-fallback warning that guarded it) is retired. Local
> development against a local world_tree sets `WORLD_TREE_URL` explicitly. Always
> verify `gald3r valk status` / `gald3r workspace token-status` after cloning a repo into a
> new workspace.

## Point This Repo at the Real API

Either of these (idempotent, safe to re-run):

```bash
# Option A — environment variable (session/CI scoped)
export GALD3R_WORLD_TREE_URL=https://api.gald3r.ai

# Option B — persistent login (writes to OS keyring / 0600 token file, never to git)
gald3r login --base-url https://api.gald3r.ai --token <bearer-token>
# --token defaults to $GALD3R_WORLD_TREE_TOKEN if omitted
```

Verify with `gald3r valk status` (connector lock state) and `gald3r workspace token-status`
(whether a session token is stored at all).

## Verb Surface (captured from `gald3r valk --help` and each subcommand `--help` — T327 ground truth)

`gald3r valk {start,status,stop,list,messages,ask,inquire}`

| Verb | Purpose | Key flags |
|---|---|---|
| `start` | Run valk-start bookkeeping: acquire the per-project single-instance connector lock, record a boot marker. Without `--detach` this is transient bookkeeping only; **with `--detach`** it spawns a real background child that stays resident driving the world_tree poll loop until `valk stop`. | `--detach`, `--poll-interval SECONDS`, `--project-id ID`, `--root PATH` |
| `status` | Report whether the connector lock is held and by whom. | `--json`, `--root PATH` |
| `stop` | Stop the running connector (if any) and clear its lock. | `--root PATH`, `--data-dir PATH` |
| `list` | List every registered Valkyrie connector across **all projects on this machine** (machine-wide registry). | `--json`, `--data-dir PATH` |
| `messages` | List (and optionally mark read) the durable events ledger (`.gald3r/valkyrie/messages/<date>.jsonl`) — every non-delegation world_tree event the connector recorded (notifications, inbound asks, inquiries). Defaults to unread-only, oldest-first. Safe no-op on an empty/missing ledger. | `--all`, `--limit N`, `--mark-read`, `--json` |
| `ask` | Ask another project a realtime peer-to-peer question (`POST /api/v1/ask`). Grounds the answer in the target project's own context (task/bug state, PROJECT.md/PLAN.md, constraints, vault snippets) and prints the answer + citations. Write-ahead queued — offline degrades to the file transport and retries on `gald3r workspace outbox flush`. | `question` (positional), `--project-id ID`, `--context-budget TOKENS`, `--json` |
| `inquire` | Typed, answerable Q&A against a project's grounded context (`POST /api/v1/ask/stream`, SSE). Same grounded-answer contract as `ask` but **not** write-ahead queued — a live stream has no replay-later semantics, so offline is reported directly. | `question` (positional), `--project-id ID`, `--context-budget TOKENS`, `--json` |

**Correction vs. the informal verb list some earlier docs assumed:** there is **no `flush`
verb under `gald3r valk`**. The outbound-queue reconciliation verb lives one level up, in the
sibling command family:

```
gald3r workspace outbox {send,pull,flush}
```

- `send` — write-ahead then push one WPAC-v2 verb message (`order|ask|event|link`) to world_tree
- `pull` — reconcile the local linking mirror against the world_tree registry
- `flush` — **reconcile-on-reconnect**: re-push every queued outbox entry (this is what
  `@g-valk-sync` wraps)

### Usage Examples

```bash
gald3r valk status --json
gald3r valk messages --limit 5 --mark-read
gald3r valk ask "Is the auth endpoint task still blocked?" --project-id gald3r_agent_dev
gald3r valk inquire "What is the current release version?" --context-budget 4000
gald3r workspace outbox flush
```

## Known Gaps (read before filing a duplicate bug)

- **BUG-238** (RESOLVED — superseded by T343) — the old `DEFAULT_BASE_URL` localhost fallback
  is gone; the default is the production host `https://api.gald3r.ai` (fails closed 401 when
  unauthenticated). See the T343 callout in the resolution-order section above.
- **BUG-235** (Low, open) — `valk ask`/`valk inquire` can return HTTP 409
  `no_provider_available` even when transport + auth are healthy (`outbox flush` reports
  `online=True`). This is an account-side AI-provider/entitlement routing gap, not a connector
  defect — do not treat a 409 here as a transport failure.

## Delegates To

Direct CLI wrapper skill — no further delegation. Commands `@g-valk-status`, `@g-valk-connect`,
`@g-valk-ask`, `@g-valk-inquire`, `@g-valk-messages`, `@g-valk-sync` all invoke this skill.
