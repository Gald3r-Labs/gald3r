# Hook: g-hk-nightly-learn

N-session learning trigger — fires the learned-facts extraction helper every
`nightly_learn_interval` sessions (T928, T1233; Python port of the retired
PS1, T1584).

## Fires On

The **stop** event: Cursor `stop` (`.cursor/hooks.json`), Claude Code `Stop`
(`.claude/settings.json`), Gemini `.agent` overlay `AfterAgent`
(`.agent/hooks.json`), and the canonical `stop` `CONCERN_CHAIN` in
`g_hk_core.py` on every fanned platform.

## What It Does

Lightweight by design: increments the per-N-sessions counter at
`.gald3r/logs/learn-counter` and only proceeds when it reaches
`nightly_learn_interval` (default 5; configurable in
`.gald3r/config/AGENT_CONFIG.md`), honors the `nightly_learn:` off switch in
HEARTBEAT.md, then spawns the heavy helper (`gald3r learn nightly`) as a
fully detached background process — the hook itself returns within
milliseconds and never blocks the agent UI waiting for LLM extraction.

## Side Effects

- Increments `.gald3r/logs/learn-counter`.
- Spawns a detached background helper process (on interval).
- Writes `.gald3r/logs/nightly-learn-last-run.log` (spawn time, PID, helper
  path, counter state) so future hangs are diagnosable.
- Never crashes the host session: any unexpected error exits 0.

## Related Tasks

- T928 / T1233 — session-summary extraction into learned-facts.md.
- T1584 — Python port of the PS1 hook fleet.
- T1628 (WS-A-5) — hook-parity lint; this companion hook.md added for the
  T1171 contract.
