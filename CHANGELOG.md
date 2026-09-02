# Changelog

All notable changes to the gald3r framework are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) ·
gald3r uses [Semantic Versioning](https://semver.org/).

> This is the **product** changelog — what changed for you. Engineering-level detail
> (internal refactors, task IDs, file moves) lives in the git history, not here.
>
> The engine has its own changelog at
> [Gald3r-Labs/gald3r_core](https://github.com/Gald3r-Labs/gald3r_core/blob/main/CHANGELOG.md).

---

## [5.0.0-beta.47] - 2026-09-02

Throne starts showing you the whole workspace, and the engine stops accepting work nobody can verify.

### Throne: see the workspace, not just the project

- A Workspace graph opens the Workspace page: every project in your workspace as a node with its name and project type, a lit indicator when that project's Valkyrie connector is running, and a badge when its project agent is fitted out. Projects the manifest names but cannot resolve are listed separately instead of silently dropped.
- The Momentum board now lives inside the Project page, so opening a project shows its totals, overview tiles and tasks by status without a detour.
- The coordinators view gains an Organization scope beside the per-project one, and tells you plainly when you do not have access to an organization's presence rather than showing an empty room.
- When world_tree is unreachable, the coordinator graph still shows a Valkyrie connector that is running on this machine.

### Throne: decisions, history and settings

- An Approvals queue on the Mission Control page lists actions agents are waiting on; approve with an optional note or reject with a required reason, backed by a durable ledger.
- Chat history is real: sessions come from a ledger with no cap and page back to the oldest one. Recording sessions from the assistant is the next step.
- The scheduler settings page shows whether the local scheduler is running, its process id and last tick, and lets you change the cadence of the two default inbox jobs.
- The AI Assistant provider picker only offers providers the app can actually chat through, and says so when saved credentials exist but none are usable.
- Every gated page uses the same upgrade affordance: required tier, reason, and a button to billing.

### Engine: acceptance criteria are part of coding now

- Claiming a task without acceptance criteria warns you; finishing it is refused until criteria exist, and one command can add them and complete in the same call.
- A review PASS on a task with no criteria is recorded as a FAIL with the reason "No acceptance criteria to test", so the item goes back to the implementer with the fix spelled out.
- `gald3r task claim` is a verb.
- Two project-agent jobs run every 15 minutes by default: the agent inbox poll and a free, local read of the WPAC file inbox. No host scheduler, no paid calls.

### Fixes

- Human-action requests sent through the ask verb now always reach the sibling project's inbox, even when the server answered.
- The WPAC inbox stops re-listing closed messages whose files were deleted.
- Throne's WebView polls carry the native session token through a host-side request, ending the false "session expired" bounce after login, and the frontend typecheck passes again.

## [5.0.0-beta.46] - 2026-09-01

Your project's agent can now address another project's agent on the event
wire — delivery still waits on a server catalog deploy.

### Ask another project

- Same-machine asks still write the local mailbox, as before.
- `gald3r project-agent ask --to-project <id> …` queues a remote question and
  flushes the outbox immediately.
- The resident Valkyrie inbox loop now drains that same outbox on every tick,
  so answers are not stranded on disk.
- You need a signed-in session. Team coordination (or the Redis coordination
  add-on) is required; solo and harvest keys are refused.
- Production `api.gald3r.ai` does not yet list the new event types in its
  catalog (checked against the live OpenAPI enum). Source has them; the
  running API does not. Until that deploy, a remote publish will be rejected.

### Board collisions, not folder sync

- Incoming field-level collisions are kept as a visible conflict log.
  Nothing last-write-wins. Status reports a pending-conflict count.
- This is not instant sync of `.gald3r/` folders, task files, or the local
  database. Server board writers stay gated.
- Do not treat this cut as a multi-user coordination product. The
  verification ladder is still the wedge.

### Left out on purpose

- No `task claim` alias, Longship chat-join, entitlement-flag seed, or
  error-intake work in this binary.
- No Postgres ingest for mailbox or conflict rows.

## [5.0.0-beta.45] - 2026-08-31

Your repo can answer you now. Talk to it from the terminal or a slash
command — same brain as Throne — instead of opening a second editor
window on the board.

### Talk to the project

- `gald3r project-agent status`, `ask`, and `chat` — or `@g-project-agent`
- Same engine Throne and the resident connector already use
- Set `GALD3R_AGENT_FITOUT` to pick the domain fit-out (terminal and Throne)
- Agents offer Valkyrie when you need a live question to another project,
  not only when you name it

### Worktrees that clean up

- Windows no longer dies on the first Permission denied from Defender,
  Cursor, or the search indexer
- Cleanup retries the lock, names leftovers that still will not delete,
  and reclaims folders git already unregistered

### Autopilot you can actually steer

- `--gauntlet` on every `@g-go*` command (off by default; same knobs as
  the autopilot loop)
- `-1` turns a numeric cutoff off — no more fake `999999999`
- Dispatch briefs can be a file path instead of a 4–5 KB paste
- A graceful stop finishes in-flight work; only `--now` abandons it
- Merged work is verified, not re-implemented from a stale bug text

### Faster lookups, safer vault

- `gald3r search` is about 10× faster on a large tree (seconds, not
  minutes) — agents stop falling back to blind grep
- Vault ingest commits the vault repo after a write, so research is not
  sitting uncommitted on disk

### New commands

- `/g-cm` — CARVER matrix for what to do next
- `/g-gilf` — senior-expert answers, no 101-level padding

## [5.0.0-beta.44] - 2026-08-28

**Your completed work stays completed.** This release closes a defect class that could silently revert already-resolved tasks and bugs during autonomous merges — closed structurally, at every layer: agent worktrees no longer see board records at all, commit safety fails closed whenever a merge or conflicted state is in progress, claim cleanup can never overwrite a resolution that landed in the meantime, and completing a task now requires its acceptance criteria ticked at write time. Autonomous runs also got dramatically faster to finish what they start: merge-gate checks across pending branches run in parallel instead of one at a time, each lane is watched individually by silence (a dead lane frees its slot while healthy siblings keep working), results credit the moment each lane reports, and known-failing merge attempts are remembered instead of retried from scratch. Your agents inherit new shipped discipline — a three-verdict verification contract for proving a fix actually works, a flake-handling protocol with a shared known-flaky-tests index, a standing merge-conflict-resolution brief, and a two-phase reviewer flow measured at a fraction of the previous review cost. Installs get cleaner too: internal maintainer content that had leaked into shipped rule files is scrubbed (upgrading overwrites the affected files), a release gate keeps it from ever shipping again, and bug routing is explicit — your project's defects go on your board, suspected gald3r defects go upstream via `gald3r gfix`. Also new: a backlog Momentum Board inside Throne, an update alert when a newer release is available, code navigation with `gald3r graph explore|impact|callers` plus an MCP equivalent, and `COMMANDMENTS.md` — an owner-editable home for your project's guiding principles.

## [5.0.0-beta.43] - 2026-08-27

**The autopilot finishes what it starts.** Completed work now merges itself — an automatic conflict-resolution ladder lands every finished branch, interrupted work is rescue-committed before anything can be lost, stranded branches get garbage-collected, and blocked items unblock the instant their blockers complete. A startup honesty gate refuses to launch on unverified board state, review verdicts apply end-to-end on their own, and high-impact closures still route through explicit confirmation instead of self-certifying. Agent lanes report liveness continuously, and context-burn gates now measure from the vendor's own transcript instead of guessing. Memory compounds between sessions: your sessions compile into a searchable project wiki automatically, and each new session starts with that catalog in context. Quality of life across the board — legacy provider configs migrate automatically with timestamped backups, `gald3r db query` gives fail-closed read-only SQL over your project database, release cuts stamp every shipped item and publish backlog momentum stats, the validator repairs previously hard-erroring status values, and the 3D entertainment stage got large-geometry batching, 72% leaner interaction hit-boxes, and character pose-rendering hardening with verified demo and broadcast modes.

## [5.0.0-beta.42] - 2026-08-26

**Your plan, your spend, your call.** Autopilot's execution model is rebuilt around billing trust: the loop now runs its workers inside the driving session by default — billed to the subscription you already pay for, never a surprise metered surface. Every launch declares each role's billing surface in color (green: your plan; blue: free external; red: real spend) with the signed-in account shown; red refuses to run without an explicit consent flag plus a confirmation, and a spending run is never silent — there's an audible cue. The platform-by-platform research behind the classifier ships with it. Skills now keep their accumulated learned notes across reinstall and update. Installer fixes straight from the field: multiple IDE overlays no longer collide, the framework guide is provisioned at install, and fresh setups build the current project layout. Plus: a one-command multi-app install plan, a live view of running agent streams, run-shape advice from your own history, portable flash-drive mode, faster duplicate-work detection, guarded record edits, and per-cut backlog health stats published in the repo.
## [5.0.0-beta.41] - 2026-08-25

**The field speaks, the same day it ships.** Every fix in this cut traces to real project reports filed against yesterday's build. Deleting a bug record can no longer wedge a project half-done — the operation is transactional on every layout, recovers cleanly from any earlier stuck attempt, and its errors now tell the truth. The autopilot work queue explains itself: items passed over by eligibility checks print the reason instead of vanishing. Commits inside agent worktrees survive a missing optional hook helper (fail-open with a note), successful-but-lingering workers are recorded as successes — with their review still scheduled — instead of false failures, and a batch of polish landed across doctor output, upgrade progress, and messaging validation. Biggest quality-of-life change: work items now carry their full story — who asked, what they asked in their own words, why it matters, what it touches — enforced at creation and readable weeks later.
## [5.0.0-beta.40] - 2026-08-23

**The loop grows judgment.** Cut hours after beta.39, this build lands the reliability batch a day of live multi-lane runs demanded: a zero-model-cost pre-review gate bounces bad handoffs in milliseconds (with the release-note requirement computed from the diff itself); a harvested implementation only earns credit once its finish gates pass on the exact commit; the supervisor's spawn ledger becomes the sole authority on agent family topology (atomic seeds, fail-closed on torn reads); interrupted bug fixes now resume on their own branch and a busy checkout defers a merge instead of discarding a finished fix. Issue harvest ships both halves — a pull consumer with local persistence and an absorb step that turns defects into inbox drafts and gates enhancements for a human. Also: the revived scheduled knowledge-ingestion system, full database rebuild and per-kind index regeneration with a matching drift heal, cache reads surfaced in cost telemetry, path-scoped search no longer paying a full-repo walk, hardened worktree containment for sandboxed workers, and the first slice of the single-writer board architecture (off by default while it soaks).

## [5.0.0-beta.39] - 2026-08-23

**An autopilot you can leave running.** Two days of monitored multi-lane runs surfaced a family of boundary failures -- work lost between runs, verified work demoted because a merge could not land, bug fixes dying at rebase for reasons that were never content conflicts -- and each is closed: interrupted implementations resume on their own branch, a reviewed PASS is never rolled back (ordinary main-branch drift now merges automatically), retired or mis-scoped merge gates no longer refuse finished work, and every change's release note survives review and lands on main. Also new: backup/restore for the project database, typed record-mutation functions and MCP update tools for every record class, vault sharing brackets with scope-aware recall, inbound messages and phone-originated steering delivered into a running session, graceful `gald3r shutdown`, cross-vendor `gald3r xreview`, and a live Backlog Momentum panel in Throne.

## [5.0.0-beta.38] - 2026-08-21

Autonomous runs now know when to stop and ask. An item that fails review three times is parked for human attention instead of being retried forever; a reviewer that gives up mid-review counts as a failed review; and database records with no backing file can no longer be offered to reviewers -- ending the loop where one broken entry starved every other piece of work.

## [5.0.0-beta.37] - 2026-08-21

**The truth-telling build.** Closes the second wave of field reports from live
multi-agent runs. Autonomous runs can no longer hang, lie, or burn silently: a
vendor CLI that stops producing output is detected within minutes and cleaned up
instead of holding a claim for hours, every run — including crashes — ends with a
final summary, cost telemetry labels unpriced usage honestly instead of showing
$0.00 (with a new breaker that halts runaway unpriced burn), and dry-run mode is
a true no-op again. The project board is harder to corrupt: constraint editing no
longer destroys definition text, dependencies/titles/descriptions are editable
straight from the CLI, and every record move regenerates the file at its
destination and verifies nothing was lost before removing the original. Hot-inbox
drafts are picked up before every agent spawn — not just once per cycle. Upgrades
stamp the version they migrated *to*, the doctor warns when the coordination
folder is invisible to git, and cross-project messages fall back to direct file
delivery when the central transport is unavailable.

## [5.0.0-beta.36] - 2026-08-20

**The earned-merge build.** Implemented work now stays off your main branch until
the independent review actually passes — a failed review leaves main untouched and
keeps the work aside for the retry, and loaded project constraints are enforced as
a hard pre-merge gate. The autopilot recognizes when an open bug was already fixed
and closes it with provenance instead of spending an implementation slot proving
there is nothing to do (field runs were losing roughly a third of their budget to
these no-ops). Parallel sessions no longer collide over shared editor config on
Windows, crashed runs no longer leave stale coordination locks (dead locks are
reclaimed automatically, with a `--break-lock` escape hatch), status history
records what the agent actually said rather than raw protocol output, and bugs
waiting on something external can now be marked **Blocked**.

## [5.0.0-beta.35] - 2026-08-19

**The tight-ship build.** Eleven verified fixes shipped the morning after the
field reports arrived: the dispatcher obeys its own eligibility math; failures
can never masquerade as successes (no-commit branches, narration, overlay-only
evidence, and admits-unchanged passes all guarded); hangs caught in minutes via
the vendor tool's own progress counter; unpriced providers fail closed so
unattended runs cannot burn unmetered; multi-line notes no longer desync the
database; teardown races no longer steal work slots; and queued drafts plus
cross-project messages are picked up at every iteration boundary.

## [5.0.0-beta.34] - 2026-08-18

**The safe-hands build.** Autopilot idle never burns money (skip + idle-iteration
limit); legitimate no-code-change fixes count as successes (no false failures or
capacity downgrades); crashed sessions' work lands on dedicated rescue branches,
never the working branch; cross-project inbox rebuilds union files with the
database so messages never vanish. New: a local push-to-talk voice preview with
transcripts always visible, subsystem-scoped agent messaging with an approve
step, richer run summaries, Windows test-infrastructure reliability, and the
complete Go backend foundation for the next-generation desktop experience.

## [5.0.0-beta.33] - 2026-08-18

The honest-numbers build: every number true, every dollar governed.

- Real cost governance: actual agent spend parsed and accumulated; the
  spending ceiling works; budgets are hard (retries and resumes count).
- No self-deadlocks: the loop's database files are guaranteed ignored
  everywhere, and automated commits can never sweep them into history.
- No false demotions: only reviews that actually ran count against a
  task; already-landed items get their free review and a real verdict.
- Truthful diagnostics: capacity messages report what happened, name
  real blockers, and every summary number derives from one source.

## [5.0.0-beta.32] - 2026-08-17

The recovery build: nothing wasted, nothing lost.

- Already-done work stays done: items whose changes already landed on
  main are detected before an agent launches (a cheap git check, not a
  paid session) and routed durably to verification; a fresh run can
  never re-offer them, and an all-excluded queue stops calmly as idle.
- Crashed agents resume their conversation: session identity is
  recorded at launch, and a watchdog-killed or crashed agent resumes
  with full working context (budget-capped, fresh-start fallback),
  with the continuity chain visible in replay.
- Agents message each other mid-run: the new `gald3r msg` surface
  delivers addressed messages between the coordinator and workers,
  durably recorded and rendered as a conversation in replay.
- Failure cleanup is complete: leftover worktrees from killed or
  crashed agents are reliably reclaimed (with or without their
  bookkeeping marker), and unmerged work is never destroyed.
- Reviews are sandboxed at the storage layer; run summaries show
  this-run counts beside all-time totals; dry-run is fully truthful.

## [5.0.0-beta.31] - 2026-08-17

The fortress build: whole classes of annoyance become impossible.

- Focus theft is over: every child process spawns through one shared
  hidden-spawn mechanism, enforced by an automated gate so the fix can
  never erode.
- `gald3r status` reorganized into grouped sections -- tasks, bugs, your
  board, suggested next actions ranked by the loop's own scoring, and
  project state -- readable at a glance.
- Health checks can no longer green-lie: validation, database sync, and
  verification enforce one shared contract; an un-ingestable record
  fails loudly at every layer.
- Doctor's version warning and its prescribed migration finally agree --
  running the fix clears the warning.
- Safer concurrent work: task/bug creation during an active run routes
  through the safe intake queue on every documented signal; Cursor
  sessions read their own context honestly.
- Brand magenta everywhere, `--color` control for piped shells, and log
  files permanently free of color codes.

## [5.0.0-beta.30] - 2026-08-16

The discipline build: branch discipline for the loop's git work, live
lane visibility, and a forensically complete ledger.

- Two opt-in branch modes: session branches collect the loop's own
  bookkeeping commits into one reviewable unit; branch-in-place runs solo
  sequential work on a feature branch in your checkout with no separate
  worktree directory. Both off by default -- nothing changes unless you
  turn them on.
- `gald3r autopilot status` shows a per-lane liveness table: which signal
  channel last showed life for each active agent; hung agents are named
  as hung.
- Every agent action leaves a durable event -- claims, verdicts, spawns,
  gate decisions -- so `gald3r autopilot replay` reconstructs any run
  with zero gaps.
- Runaway-protection counters measure consecutive trouble since the last
  productive iteration, never lifetime totals -- long healthy runs can no
  longer accumulate into a false stop.

## [5.0.0-beta.29] - 2026-08-16

The trust build: verdicts are law, the docs are professional, nothing
internal leaks.

- A reviewer's written verdict can never be suppressed because its prose
  resembled an error message; items whose reviews never conclude park for
  human attention after three attempts.
- The documentation site rebuilt: dedicated Commands / Skills / Agents /
  Verbs pages, headliner navigation, full currency, and a permanent
  sanitization layer so internal references can never reach a public page.
- Session goals, the codename registry, and five decision-framework
  commands now have their slash-command surfaces in every IDE overlay.
- Generated configuration templates carry plain product comments only.

## [5.0.0-beta.28] - 2026-08-16

The resilience build -- plus a thinking toolkit and two navigation aids.

- One stuck task can never crash a run: root fix, graceful refusal, and a
  recovery net around the scheduler.
- Budget exhaustion finishes in-flight work (merge + review) before ending;
  leftovers report honestly in one line.
- Blocked work stays blocked -- every dependency mechanism honored through
  one shared rule.
- `gald3r autopilot replay RUN_ID`: reconstruct any past run from its
  durable records -- debugging is one command, not archaeology.
- Session goals (`gald3r sesh-goal`): tell the AI where the session is
  headed and it holds the course.
- Codename registry (`gald3r codename`): internal names mapped to plain
  ones -- resolve "that thing that does X" to its real name instantly.
- Five decision frameworks: g-thinker, g-ooda, g-mdmp, g-ipb, g-stz.
- Agent child processes no longer flash console windows or steal keyboard
  focus on Windows.

## [5.0.0-beta.27] - 2026-08-16

The supervision build: a running loop is either shipping work or telling
you exactly why not -- never silently spinning.

- Reviews finish everything: bug fixes get fresh-eyes verdict turns too,
  so completed-but-unverified work drains instead of accumulating
  (`gald3r go-bug-review`).
- Fresh work outranks repeat offenders: the picker remembers, across
  runs, which items keep producing no real change and demotes them --
  never drops them.
- Safety gates always arm: missing provider telemetry now falls back to
  computed proxies (wall-clock, iteration count, output volume) with a
  once-per-run banner saying exactly which gates run on what; a run that
  iterates without completing anything trips a no-progress breaker.
- Silent workers get reclaimed: liveness now reads real work signals
  (board writes, worktree activity) -- a quietly-working agent lives, a
  wedged one is killed, named, and its lane refills immediately.
- Worker agents can no longer stop the loop that spawned them.
- Briefs trust your board: a task's own recorded notes outrank any stale
  repository document that contradicts them.
- `gald3r doctor` and the running loop now agree on workspace
  participation via one shared detection rule.

## [5.0.0-beta.26] - 2026-08-15

The throughput build: the loop spends its budget on work an agent can
actually finish, and hands everything else to you -- once.

- Human-gated items park in your attention queue after one attempt
  instead of being re-implemented forever; every item caps at three
  attempts per run with a named reason.
- The picker never offers human-gated or already-merged work, and
  parallelism holds at your --lanes setting even when a worker dies.
- Windows: worktree markers ride through antivirus file locks; repos
  that keep .gald3r/ out of git stop seeing refused staging messages.
- Run backlog-curate before your first beta.26 loop so the whole
  budget goes to real, landable work.

## [5.0.0-beta.25] - 2026-08-15

The stability build: state reconciliation, safe upgrades, and budgets
that mean what they say.

- Budget in one sentence: the number of tasks and bugs the loop will
  attempt to handle. Reviews never consume budget, and completed work
  gets reviewed and finalized before anything new starts.
- The board never lies: failed or empty merges roll back and requeue,
  claims release themselves, killed workers leave logs and ledger
  events, and end-of-run summaries report real PASS/FAIL counts.
- Safe upgrades: install update detects wrapper scripts on PATH and
  updates the real install; doctor flags stale copies and mismatches.
- MCP servers launch reliably: generated configs point at the exact
  installed binary, not a PATH search.
- Every guide and playbook now uses the plain gald3r command -- no
  Python environment is ever required.

## [5.0.0-beta.24] - 2026-08-15

Autopilot reviews each finished item in the same loop. Harvest keeps completed task files.

- Autopilot now reviews each finished item in the same loop instead of waiting for a later batch pass.
- Completed task files survive harvest. Leftover scratch files and local scheduler or vault-ingest state no longer stop a run.
- Worktrees keep the controller board database. Child checkouts no longer rebase shared board indexes onto main.

## [5.0.0-beta.23] - 2026-08-14

Autopilot runs implementers in parallel. Vault-first research is on.

- Autopilot runs implementers in parallel by default. Use `--no-code-swarm` for one-at-a-time. Sibling count defaults to 5 (recommended 3–8). `--budget` is an attempt cap; `0` means unlimited.
- Agents search the local knowledgebase before the internet. Memory recall treats ingested research notes as first-class results.
- A local scheduler can wake HEARTBEAT rows without keeping Throne open. Doctor `--apply` upgrades a legacy WPAC inbox.

## [5.0.0-beta.22] - 2026-08-14

g-go stays on the model you launched from. Autopilot names its models up front.

- `g-go` / `g-go-code` / `g-go-review` inherit the IDE you are in. They no longer switch to a pinned model from project config.
- Autopilot (`gald3r autopilot loop` / `@g-go-go`) requires `--provider` and `--model` (or the per-role flags) and prints which model each role will use before it starts.
- BUGS.md is a slim table of links, matching TASKS.md. Repair an already-swollen index with `gald3r bug regenerate-index --apply`.

## [5.0.0-beta.21] - 2026-08-13

Field fix so a live autopilot loop can finish and harvest.

- Allowlisted board-file writes mid-loop no longer block harvest or the next worktree.
- A title-only Critical bug is skipped instead of claimed-then-refused, so it does not trip the capacity breaker or reopen paused/resolved work at teardown.
- Autopilot coordinator and implementer children now see the project directory Claude hooks expect.

## [5.0.0-beta.20] - 2026-08-13

Autopilot now runs multiple implementers at once.

- `gald3r autopilot loop` / `@g-go-go` fans out coding agents in parallel by default. Use `--no-code-swarm` when you need one-at-a-time.
- Merge-back stays serialized so parallel worktrees do not wedge the git lock.

## [5.0.0-beta.19] - 2026-08-13

The sequential-path survivability release: one loop, honest go-bug, live bucket logs.

- Silent buckets are killed after 30 minutes by default (was 5); the heartbeat can see bucket output, and a still-running bucket writes a live log.
- `VERDICT: FAIL` keeps the bug open. Empty specs fall back to the file/database. Title-only Critical bugs are not dispatched. Isolated-worktree briefs tell the agent to commit on that branch.
- A second `autopilot loop` is refused while one is alive. Graceful stop skips remaining buckets and kills the in-flight one after three minutes. Starting a new loop releases leftover go-bug claims from a previous binary.
- Implementer briefs name configured MCP servers (host:port only). `install update` lists leftover gald3r PIDs after rename-aside. Windows INFO lines no longer show up as crash spam.

## [5.0.0-beta.18] - 2026-08-13

Docs match the binary: `@g-go-go` runs one implementer at a time. Parallel
coding is `@g-go --swarm`, not a hidden loop flag.

Field reports (`gald3r gfix`) warn in the draft itself when GitHub CLI cannot
auto-file, fill watchdog evidence from the last captured kill when you type the
class by hand, and refuse to auto-file an empty watchdog report unless you pass
`--force`.

## [5.0.0-beta.17] - 2026-08-13

The field-follow-up release: a finished turn is trusted over plumbing noise.

- A completed no-commit turn counts as real work, so a correct "nothing to
  change" triage no longer trips the capacity breaker and kills a run that
  still has queued work. Claims from buckets that die at run-end are released
  instead of occupying worker slots forever.
- On Cursor, review without an explicit provider prefers the Cursor agent
  over a missing local model. A transport error is a run problem, not a mass
  FAIL of every task under review. A complete implementation is not marked
  failed because teardown hit a brief unauthorized blip. Textual review
  verdicts still count if the JSON file write is blocked.
- `constraint add --rule-file` works without a dummy argument; update and
  delete can repair a bad row. `gfix` warns at draft time if GitHub CLI is
  missing or not logged in.
- Git applies to the main checkout wait on an index lock and retry instead
  of deleting the lockfile.

## [5.0.0-beta.16] - 2026-08-12

The complete-briefs release: spawned agents now receive their entire
instructions, every time, at any size.

- Agent briefs (coordinator, implementer, reviewer) are delivered whole via
  file handoff instead of being squeezed through OS command-line limits --
  no more truncated instructions on any platform, and every delivered brief
  is kept on disk so you can see exactly what an agent was told.
- Windows launcher shims (used by some agent CLIs) are detected and routed
  to file delivery automatically, even for small briefs.
- Every free-text CLI option now accepts --<flag>-file PATH and '-' for
  stdin, so multi-line content never fights shell quoting.
- gald3r selftest now validates hook wiring for every installed platform
  overlay, understands the opt-in git-hooks setup, and checks active
  constraints; gald3r doctor flags stale or shadowed gald3r binaries on
  PATH, including version mismatches.
- Local AI docs now cover Unsloth Studio setup alongside Ollama, LM Studio,
  vLLM, and llama.cpp.

## [5.0.0-beta.15] - 2026-08-12

The report-it release: real throughput on every configuration, and a
one-command way to tell us when anything still goes wrong.

- Worker agents are invoked correctly for non-interactive use across every
  supported agent CLI -- the missing print-mode and trust flags explained
  both the silent hangs and the "completed but changed nothing" runs. A
  worker that produces zero output is now honestly counted as a failure,
  and every worker's own output lands in its per-task log.
- Stale working copies refresh themselves before dispatch, so finished work
  always merges; stopping a run releases exactly the claims it interrupted.
- NEW: `gald3r gfix` -- when something fails, gald3r drafts a complete bug
  report from its own logs, scrubs personal information automatically (and
  shows you what it removed), lets you edit the draft, and only files a
  prefilled GitHub issue after your explicit confirmation. Duplicates are
  detected and pointed at the existing issue. You choose the offer level
  once: off, critical-only, or all.

## [5.0.0-beta.14] - 2026-08-12

The throughput release: the last field blocker is dead, and projects get a
cleaner shape plus three new ways to capture work.

- Worker agents now receive their FULL instructions (task description,
  acceptance criteria, working contract) instead of a title-only fragment,
  and Windows PowerShell-script-installed AI CLIs launch correctly -- the
  defect family behind every silent stall since beta.3, root-caused by the
  beta.13 diagnostics and proven fixed on the exact failing configuration.
- Cleaner project layout: SDLC files live under .gald3r/project/; existing
  projects keep working and migrate only when you choose (gald3r layout
  migrate, dry-run by default).
- NEW: per-file Ideas with a regenerated board, a user-only TO-DO commitment
  tier (idea -> to-do -> task lifecycle), and Architecture Decision Records
  with an immutable supersede chain. PRDs repaired end-to-end.
- NEW: Record a Skill -- demonstrate a workflow once inside a recording
  window and gald3r compiles it into a real, invocable skill.
- First-supporter integration for Unsloth Studio as a built-in local
  model provider.
- Stop orders are scoped to their run; stale ones can no longer consume a
  fresh launch. Harvested work no longer drags transient markers into main.

## [5.0.0-beta.13] - 2026-08-12

The restored-playbook release: the autonomous loop got its full operating
knowledge back -- and proved it live before shipping.

- The autopilot coordinator's internal briefing is whole again: restored
  from the era when multi-hour unattended runs just worked, carried inside
  the binary, and adapted to the current engine. Coordinators receive
  complete work-item detail up front and delegate immediately instead of
  re-reading the project or quietly doing everything themselves.
- Every built-in pipeline playbook was audited line-by-line against its
  proven predecessor; dozens of lost operating rules are back, and every
  "the binary enforces this" claim was verified against the actual code --
  the untrue ones now say honestly what is and isn't automated yet.
- `gald3r go-preflight` genuinely performs its documented safety checks:
  cross-project inbox conflict detection and a clean-status sweep across
  workspace member repositories, with clear remediation output.
- Proven before the cut: a real end-to-end autonomous run on this exact
  build -- live coordinator, live worker agents, three tasks implemented,
  independently reviewed, and completed, with a clean halt.

## [5.0.0-beta.12] - 2026-08-11

The eyes-and-teeth release: a stalled swarm can no longer hide, and
stopping one actually stops it.

- A worker that produces nothing gets caught: a per-worker liveness
  watchdog kills any bucket that goes silent, reports what it captured,
  and the loop MOVES ON to the next item instead of freezing forever
  behind one wedged process. The heartbeat now ticks through the entire
  dispatch window, so a quiet run always tells you it is alive.
- `gald3r autopilot stop --now` is genuinely immediate: it terminates
  the recorded process tree and finalizes the run marker itself -- no
  more killing by PID and hand-editing files to recover.
- Honest events: `bucket_planned` (intent) is now separate from
  `bucket_spawned` (worker confirmed running), so telemetry can never
  again claim five workers dispatched when none started.
- Claude-subscription users get autonomous implementers: `--provider
  claude` now genuinely drives the claude CLI instead of silently
  demanding an API key -- proven end-to-end with a real agent fixing a
  real bug before this release was cut.
- Every shipped @g-* command works as written: ten internal playbooks
  the commands reference are now retrievable, guarded by a test that
  walks every shipped command; and a mistyped subcommand errors with a
  did-you-mean across all 55 command groups instead of silently
  printing help.

## [5.0.0-beta.11] - 2026-08-11

The unblocked release: every kind of repo can loop now.

- The one-second bucket deaths are over. If your project gitignores its
  .gald3r/ folder -- the normal setup for application repos -- spawned
  workers used to land in a workspace with no task specs at all and die
  instantly. gald3r now detects that shape and points every worker at
  the real project state automatically, with a clear line in the log
  saying so.
- The @g-go command fallback works again: the instructions those
  commands fetch are no longer refused by the assistant-facing gate.
- Backup archives can no longer dirty your tree and block a run -- the
  ignore rule now heals itself at loop start, no reinstall needed.
- Memory upgrades: per-agent memory loadouts (give your reviewer and
  implementer different working memory), a skill-extraction pipeline
  that distills reusable skills from completed work (human-approved
  before anything ships), and session-local notes no longer leak into
  memory recall.

## [5.0.0-beta.10] - 2026-08-11

The delivered-orders release: spawned agents finally receive their instructions.

- The brief actually reaches the agent now. Headless CLI agents
  (cursor-agent, claude) were being launched without their
  instructions -- a real agent would run for minutes and change
  nothing. The prompt is now handed over the way those CLIs expect,
  so implementer and coordinator turns do the work they were asked to.
- Failures tell you why. Every loop-spawned worker's output is
  captured to a per-run log and the failing lines are quoted in the
  failure message -- no more bare "exited 1" with nothing to act on.
- What you asked for is what runs: the resolved provider and model
  travel explicitly with each spawned worker, and go / go-code /
  go-bug / go-review all accept --provider directly.
- Review runs on subscriptions too. The reviewer role can now drive
  cursor-agent, so verification passes work on a machine with no API
  keys -- and a verdict is only accepted from real recorded evidence,
  never from a clean exit code.
- Quality of life: crash telemetry and backup archives can no longer
  dirty your working tree or block a run, and the docs gained a cost
  guide for choosing how you loop (in-session pipelines vs spawned
  CLI sessions vs API-key providers).

## [5.0.0-beta.9] - 2026-08-11

The throughput release: your subscriptions now do the work.

- Autonomous implementers on subscription credentials: go-code and
  go-bug can now drive the same cursor-agent/claude CLI your
  subscription already pays for -- no API keys required. On a
  subscription-only machine, autopilot buckets actually implement and
  fix instead of failing in one second (the root cause behind every
  zero-throughput run since beta.3, found by beta.8's own diagnostics).
  A do-nothing agent can never fake a fix: evidence of real change is
  required before anything resolves.
- A doomed run refuses at startup with the remedy named -- before
  claiming work or creating worktrees -- and the circuit breaker names
  the shared cause when every failure is the same one.
- Review phase unstuck: awaiting-verification work dispatches again
  (the empty-queue miscount that let review items age forever is
  fixed).
- Harvest merges for real: diverged-but-clean bucket branches land via
  a proper merge commit; genuine conflicts surface exact copy-paste
  recovery commands. The first-merge-strands-the-rest era is over.
- Live run events can stream to world_tree subscribers (opt-in
  --publish-events; durable offline queue, never slows a run).
- Component activation telemetry is back (crash-stats records real
  usage again), config hot-reload is race-free on Windows, backup zips
  and telemetry logs can no longer block a run's preflight, and every
  shipped verb now has documentation enforced by CI.

Update: gald3r install update

## [5.0.0-beta.8] - 2026-08-10

The observability release: a swarm can never run dark again.

- Live event stream: every autopilot run now narrates itself the moment
  things happen -- claims, agent spawns, merges, harvests, breakers,
  costs -- as [AUTOPILOT][EVENT] lines in your session AND a durable
  per-run event ledger. New: gald3r autopilot events --follow tails a
  live run from any other terminal.
- Heartbeats and a stall watchdog: long iterations now beat every 15
  minutes with liveness diagnostics, and a frozen coordinator (the
  74-minute silent-stall class) is detected within minutes -- claims
  released, one retry, then a loud named halt. Never an hour of
  silence.
- autopilot status now tells the truth: it reads the same candidate
  board the loop itself uses (it previously read an unrelated legacy
  queue), and task show --json exposes claim ownership.
- Every Windows binary now has a face: Mjolnir-derived icons and real
  Gald3r Labs version metadata in Explorer, Task Manager, and
  Add/Remove Programs.
- Find your platform: 37 new docs pages -- one per supported platform
  -- at docs.gald3r.ai, matching the new Supported Platforms section in
  this README.
- Config hot-reload no longer races itself on Windows; a new CI gate
  guarantees every shipped verb has documentation.

Update: gald3r install update

## [5.0.0-beta.7] - 2026-08-10

The harvest release -- and Longship's debut: finished work always comes
home, and the Agentic Focus Terminal is now in the box.

- The harvest gate: work an autopilot agent completes in a worktree is now
  automatically committed and merged into your checkout -- at every
  iteration close and once more at run end. A merge that is not safe leaves
  the work preserved on its own branch, never destroyed, with a line naming
  why. Runs can no longer report "zero work" while finished code sits
  stranded.
- Longship ships in every install bundle: gald3r-longship, the terminal
  chat app, is now an eighth signed binary in the platform archives -- with
  a guided first-run: launch it with zero config and it walks you through
  picking a provider (a running Ollama or LM Studio is offered as the
  no-key instant path), then drops you straight into chat. No more fatal
  error before you even see the app.
- gald3r context now binds to the CALLING session's own transcript and
  never guesses -- previously, on a machine with several live sessions, it
  could silently measure a different session and report it as real. Cursor
  sessions get their own measurement source with the same honesty contract.
- Stale claims release themselves at run end; the worktree janitor no
  longer abandons a sweep at the first dirty worktree; long healthy
  iterations can no longer be killed by a stop-escalation ceiling shorter
  than the coordinator's own timeout; and every cost figure says
  "(estimated)" when it is one -- with real per-model pricing now wired
  into the loop.
- upgrade-project --dry-run is now truly read-only (it previously refreshed
  the overlay and wrote a backup), upgrades take an automatic pre-flight
  backup, search --path accepts a single file, and a mistyped task/bug
  subcommand tells you what it was and suggests the closest real one.

Update: gald3r install update

## [5.0.0-beta.6] - 2026-08-10

The autopilot integrity release: bugs are workable, work is unlosable,
parallelism is honest, and local AI works out of the box.

- New gald3r go-bug: autopilot can now FIX bugs, not just log them -- the
  full claim, agent turn, self-verify, resolve cycle, wired into
  deterministic dispatch. A bug backlog becomes reachable work and
  --min-severity finally gates something real. An empty bug queue no longer
  ends a run while tasks remain.
- Rescue commits: if a run dies mid-iteration (provider refusal, breaker,
  fatal signal), uncommitted run-authored work lands in a named wip(rescue)
  commit -- never lost to a cleanup, and never touching your own
  pre-existing uncommitted edits.
- Honest parallelism: implementer counts only count buckets that actually
  landed work; idle or failed buckets are loudly diagnosed; a dispatch that
  produces nothing counts as a capacity violation (consecutive AND
  cumulative breakers).
- Local AI out of the box: gald3r init-providers discovers a running Ollama
  server over HTTP (no CLI needed), the documented setup path just works,
  and the .gald3rsecret no-cloud tier correctly treats loopback AI as local
  (LAN endpoints require an explicit opt-in).
- New CI parity gates: advertised flags and documented environment
  variables are now mechanically verified against the binary on every
  change -- the lost-surface defect class is structurally dead.

Update: gald3r install update

## [5.0.0-beta.5] - 2026-08-09

Provider routing release: a rate-limited AI provider no longer stops your work.

- The autopilot coordinator is no longer hardcoded to the Claude CLI: a Cursor
  host defaults to cursor-agent, and the full routing surface works -- CLI
  flags (--provider/--model plus per-role --coordinator/--implementer/
  --reviewer -provider/-model), all six GALD3R_GGO_* environment variables,
  and AGENT_CONFIG keys, with a documented precedence order (flag beats env
  beats config beats host default).
- Hit a provider quota wall mid-run? The run no longer dies: the refusal
  costs no budget, gald3r falls back to a healthy configured provider (opt
  out with --no-provider-fallback), and if nothing is available it stops
  honestly with the provider's own quota-reset time, a distinct
  PROVIDER_UNAVAILABLE state, and exit code 4.
- cursor-agent runs now report token counts and honor the context-exhaustion
  safety stop.

Update: gald3r install update

## [5.0.0-beta.4] - 2026-08-09

- gald3r install update works again: downloads the per-platform archive,
  verifies it against SHA256SUMS.txt (fail-closed), extracts, and replaces the
  running binary safely. Sibling binaries you already have are refreshed too.
  (This fixes beta.3's known issue -- one last manual install gets you here.)
- Intel Macs no longer download the Apple Silicon build by mistake.
- Autopilot's deterministic dispatch now merges to your repo's actual branch
  (master/trunk/anything), not a hardcoded main.
- Engine CI is fully green on Linux again; one real SDK fix landed on the way
  (missing-executable errors now surface as the typed NOT_FOUND error on all
  platforms).

## [5.0.0-beta.3] - 2026-08-09

Autopilot economics release: the swarm now materializes.

- Deterministic implementer dispatch: when a coordinator ends an iteration with
  zero implementers despite runnable work, the outer loop provisions implementer
  runs itself (worktree-isolated; opt out with --no-deterministic-dispatch).
- Capacity circuit breaker: consecutive advertised-but-unmaterialized capacity
  halts the loop with exit code 3 instead of silently burning the budget
  (--capacity-violation-limit, --no-capacity-breaker).
- Review-phase iterations are skipped for free when nothing awaits verification.
- Iteration accounting diffs the git checkpoint: real commits are never reported
  as zero throughput again.
- gald3r run --approval-mode=ask: stream-json tool calls can require an
  approval_request/approval_response round trip on stdin (fail-closed on
  timeout or closed stdin).
- Known issue: 'gald3r install update' in fielded builds requests a retired
  asset name and fails (BUG-774, fix in the next beta) -- update by running
  the installer for your OS from the releases page instead.

## [5.0.0-beta.2] - 2026-08-09

- Release assets consolidated to one archive per platform with version-less
  names, so /releases/latest/download links never go stale.
- Signed installers: Windows .msi (Authenticode), macOS .pkg (Developer ID +
  notarized), Linux tarball with install.sh.

## [5.0.0-beta.1] - 2026-08-09

The Go rewrite. The engine is now a single fast native binary on every platform:
startup drops from 8-11s to ~120-190ms; no Python, no runtime to install.

- .gald3rsecret: keep sensitive files out of AI prompts, logs, and the cloud.
- .gald3rignore gains ! re-include negation.
- Restored/added verbs: search, validate, context, task next, task stale-claims.
- Auto-backup before schema migrations; safer upgrade path.

## [4.0.0-beta.3] - 2026-08-05

**The first three-platform signed release — and the storefront becomes a front door.**

### Added
- **Direct per-OS download table** on the README (installers and binaries, always resolving to
  the newest release) and a **`The gald3r system — who does what`** map: every user-visible
  capability of the product family and which piece owns it (`gald3r_core`, `gald3r_throne`,
  `world_tree`, the framework, `gald3r_longship`).
- **`PLATFORM_SUPPORT.md`** — the 38-platform support matrix as native Markdown, ported from
  the hand-verified canonical matrix with **the honest gaps marked** (what does not function
  today, and which of those are tracked follow-ups versus platform limitations). Replaces the
  old `PLATFORM_SUPPORT.html`, which rendered as unreadable raw HTML on GitHub.

### Changed
- **The repo is now a landing page, not an install dependency.** Everything that used to ship
  here as file trees — the per-platform overlays and the project template — is generated by the
  binary (`gald3r platform install <platform>`), always current with your binary version. The
  README was rewritten around that flow, with install paths for all three OSes.
- **The `.pkg` installer is now signed at the container level** (Developer ID Installer), so
  macOS no longer shows the unsigned-developer confirmation; the binary inside was already
  codesigned and notarized.

### Removed
- **14,702 legacy files**: `platforms/` and `project_template/` (provisioned by the binary
  now), the pre-4.0 clone-and-copy instructions and `setup_gald3r_project.*` scripts, old
  `releases/` notes, `ROADMAP.md`, `PLATFORM_SUPPORT.html`, and two generated matrix files
  whose canonical copies live in the engine repo.

## [4.0.0-beta.2] - 2026-08-03

### Added
- **Prominent Windows/macOS/Linux support statement** on the README and a direct link to the
  new docs site, [docs.gald3r.ai](https://docs.gald3r.ai).
- **`docs/IP_PURGE_PLAN.md`** — the options, exact commands, and consequences for a git-history
  scrub of the retired `project_template/.gald3r_sys` payload (BUG-639), left as an owner
  decision; the runbook has since moved to the engine repo's docs.

### Fixed
- **`PLATFORM_SUPPORT.html` pointed at 34 dead links.** Every platform card linked to a
  `github.com/Gald3r-Labs/gald3r_platform_<name>` repo — none of those repos exist (verified
  against the full `Gald3r-Labs` org roster). This repo is, and has been, a single monorepo:
  every platform's payload lives in `platforms/<name>/` right here. Cards now link to the real
  in-repo folders, cover all 38 shipped platforms (4 were missing: `mimo-code`, `pi`, `zcode`,
  `zed`), and the page's own copy no longer implies a "clone the repo you use" multi-repo model.
- **Corrected the platform count from 39 to 38 everywhere** (README badges/table/bullets,
  `CHANGELOG.md`, `PLATFORM_SUPPORT.html`) — `platforms/` has 38 real overlay directories; the
  prior count included `PLATFORM_REGISTRY.yaml` itself as if it were a platform.
- **`PLATFORM_CAPABILITY_MATRIX.md`** cited a `strategy/gen_platform_docs.py` generator, a
  `strategy/PLATFORM_DATA.json` source, and a `COMBINED_READINESS.md` companion — none exist in
  this repo. Removed those dangling references, corrected its own platform count (34 → 38),
  added the missing `mimo-code` row, and fixed two directory-name typos (`kilo_code` →
  `kilo-code`, `kiro_cli` → `kiro-cli`). The per-platform ✅/⚠️/❌ capability cells were not
  re-verified in this pass — see the file's own reconciliation note.

### Removed
- **`PLATFORM_COMBINED_READINESS.md`** — an orphaned doc (no incoming links from README or
  anywhere else) describing the same retired 34-platform, separate-repo-per-platform model as
  the dead `PLATFORM_SUPPORT.html` links above, sourced from a `strategy/PLATFORM_DATA.json`
  file that doesn't exist in this repo.

### Changed
- **`project_template/.gald3r_sys` removed from tracking** (328 files, ~45,000 lines) —
  compiled-into-binary IP that should never have shipped as loose source (BUG-639). `.gitignore`
  now guards against it coming back.
- **Every shipped reference to the retired `.gald3r_sys/schemas|scripts` tree** now points at the
  current native `gald3r` CLI surface instead (`gald3r schema-migrate`, `gald3r lint
  post-write`, etc.) across all 38 platform overlays and `project_template` (BUG-598) — an
  in-flight sweep that had been sitting uncommitted; reviewed file-by-file and confirmed every
  referenced verb actually exists before committing.
- **Corrected two stale component counts**: agents was miscounted as 15 (it was counting two
  non-agent index files alongside the real 13 `g-agnt-*` definitions); rules is 13, not 12, now
  that `g-rl-33-enforcement_catchall` is committed rather than sitting in the uncommitted sweep.

---

## [4.0.0-beta.1] - 2026-08-01

**gald3r becomes a matched pair: framework + compiled engine.**

### Added
- **A signed, compiled engine.** The deterministic core that runs task and bug lifecycle,
  validation, the local database, and multi-agent orchestration now ships as a single signed
  binary from [gald3r_core](https://github.com/Gald3r-Labs/gald3r_core/releases) — with a
  Windows MSI installer. No Python toolchain required.
- **38 supported AI coding platforms**, up from 34.
- **13 specialized agents** for review, verification, QA, and infrastructure work.

### Changed
- **Version line unified.** "gald3r 4.0" now names the framework and the engine together.
  Version 3.x was template-only, installed per IDE; 4.0 is the first release where the two
  ship as one product.
- **Shipped component counts:** 116 skills, 182 commands, 38 hooks, 13 rules.
- **Install guidance split by product.** The framework installs from this repo; the engine
  installs from `gald3r_core`; the desktop app installs from `gald3r_throne`. Each product
  is fetched from its own release channel.
- **README rewritten** around what gald3r actually does for you rather than what it contains.

### Fixed
- Corrected repository links throughout the documentation (the project moved to the
  **Gald3r-Labs** organization).
- Repaired broken links to the platform support matrix and release notes.

---

## [3.0.0] - 2026-07-06

**The framework goes Python-first.**

### Changed
- Helper scripts that previously shipped as loose files are now built into the engine —
  fewer moving parts in your project, and the same behavior on every platform.
- Platform verification became a first-class capability: check an installed platform tree
  in place, with an HTML report card.

### Fixed
- Eliminated character-encoding corruption in shipped template files, with a guard to keep
  it from returning.
- Fresh installs no longer create stray placeholder directories.

---

## [2.4.0] - 2026-06-27

### Added
- One-command installs for the companion apps, downloading signed builds from public
  release channels with integrity verification before anything is written to disk.

### Fixed
- Install integrity can no longer fail open: a missing or tampered signature stops the
  install loudly instead of proceeding silently.

---

## [2.3.0] - 2026-06-25

### Changed
- Completed the migration from PowerShell to Python across the framework — one codebase,
  identical behavior on Windows, macOS, and Linux. Roughly a thousand redundant scripts
  were removed from the shipped payload.
- Task IDs in `TASKS.md` are now consistently formatted.

---

## [2.2.0] - 2026-06-24

### Added
- The autonomous work conductor streams live progress to your terminal instead of running
  silently.

### Fixed
- The conductor now halts on coordinator failure rather than burning through its remaining
  budget on repeated errors.

---

## [2.1.2] - 2026-06-23

### Added
- A comprehensive pre-flight backup before any upgrade is applied.

### Fixed
- Upgrades no longer deprecate removed components by default — that behavior is now opt-in.
- Version reporting no longer shows stale numbers after an upgrade.

---

## [2.1.1] - 2026-06-23

### Added
- **Plugin lifecycle management** — install, remove, list, and update gald3r plugins.
- **Vault knowledge tools** — structured note retrieval and backlink queries over your
  project's knowledge base.
- **Selectable vault location** — user-level, workspace, or per-project.

---

## [2.1.0] - 2026-06-20

### Added
- Per-platform test harness with an HTML report card.
- Unified identity provisioning on first run.
- A canonical hook event set shared across platforms.

### Fixed
- Generated projects no longer ship build artifacts or virtual environments.

---

## [2.0.1] - 2026-06-10

### Changed
- Copyright transferred to Gald3r Labs LLC across all repositories.
- Default organization updated to **Gald3r-Labs**.
- Platform repositories now publish GitHub Releases by default.

---

## [2.0.0] - 2026-06-04

**The engine arrives.**

### Added
- **A file-first engine** driving every system — tasks, bugs, vault, releases — deterministically,
  with zero LLM calls.
- **A command line** (`gald3r task new`, `gald3r bug new`, …) so you can drive the same state
  from a shell or a script.
- **An MCP server** exposing those operations as tools to any MCP-capable agent.
- **`gald3r doctor`** — a read-only health check for your installation.

---

## [1.10] - 2026-06-02 — *Cursor + Claude Unity Edition*

### Added
- All 34 platform adapters moved into this repository.
- `--platform <name>` installer flag to target a single platform.

### Changed
- Restructured the install model around a single `project_template/` directory you copy into
  your project.

---

## [1.0.0] – [1.9.0] · 2026-05

Early releases: the initial `.gald3r/` brain structure, the first skill and command sets,
Cursor and Claude Code support, and the installer scripts. Full detail is in the git history.
