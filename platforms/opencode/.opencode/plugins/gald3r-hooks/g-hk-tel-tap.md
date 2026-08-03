# Hook: g-hk-tel-tap

TEL (Terminal Event Layer) host-CLI hook tap (T90; Claude Code first).
Maps host hook events onto the TEL normalized stream via
`gald3r_core.core.tel.host_adapter` -- matches active rules, applies
ledger-scoped redaction, and captures survivors to a topic-routed TEL
capture ledger. D001 templates_dev CRASH-surface gate RATIFIED by the
owner (wrm3) 2026-07-13.

## Fires On

Registered twice in `g_hk_core.CONCERN_CHAIN`, once per supported kind:

- `CONCERN_CHAIN["tool-end"]` with `--kind post_tool_use` -- fires from
  Claude Code's `PostToolUse` (via `g-hk-on-tool-end.py` ->
  `g_hk_core.dispatch("tool-end")`).
- `CONCERN_CHAIN["stop"]` with `--kind transcript` -- fires from Claude
  Code's `Stop` (via `g-hk-on-stop.py` -> `g_hk_core.dispatch("stop")`),
  which carries `transcript_path`.

`--kind statusline` is supported by this script and by
`core.tel.host_adapter` for direct/manual invocation only -- it is
deliberately NOT registered against Claude Code's actual `statusLine`
command config in this task. See "Statusline scope boundary" below.

## What It Does

1. Reads the harness's stdin JSON payload (`_hook_common.read_stdin_json`).
2. Resolves `gald3r_core.core.tel.host_adapter` (dev-checkout import first,
   installed/frozen `gald3r` engine namespace via
   `_hook_common.bootstrap_engine()` as fallback) and builds a
   `TelRenderPipeline` via `host_adapter.build_host_pipeline(root)`.
3. `--kind post_tool_use` / `--kind statusline`: feeds the raw payload
   through `host_adapter.handle_host_event(kind, payload, pipeline=...)`
   once.
4. `--kind transcript`: reads `transcript_path` off the payload, tails the
   JSONL transcript for lines added since the last persisted offset
   (`.gald3r/logs/tel_transcript_offsets.json`, keyed by resolved
   transcript path), and feeds each new raw JSONL record through the
   adapter as its own `transcript` event -- no filtering/extraction; a
   project wanting to drop noisy lines (sidechains, routine tool results)
   writes a `#gag` rule for them instead.
5. A record survives (is written to its `host_{kind}` capture ledger topic)
   unless an active `#gag` rule matched its projected line -- gag
   suppression is the primary noise-reduction mechanism for this tap (see
   `core.tel.host_adapter`'s module docstring "Design choices" section for
   why this differs from the render-path-fed ledger sinks' "never drop"
   philosophy).

## Side Effects

- May append one line to `$GALD3R_HOME/tel/captures/host_post_tool_use-*.log`,
  `host_statusline-*.log`, or `host_transcript-*.log` per event that
  survives gag suppression.
- May write/update `.gald3r/logs/tel_transcript_offsets.json` (transcript
  kind only).
- May append a diagnostic line to `.gald3r/logs/hook_diag.log` on a
  degraded/no-op path (engine unresolved, tap error). Never writes
  anything else.
- **NEVER prints to stdout, under any circumstance.** Not even the
  `{"continue": true}` / `"{}"` envelope other concern hooks use -- see the
  script's own module docstring for why (token-injection trap for
  `tool-end`/`stop` concern chains). Always exits 0.

## Statusline scope boundary

tel_plan.md treats the visible status bar as an OUTPUT-direction feature
(future `#statusbar` rules reading FROM the TEL variable store), not this
task's INPUT tap. Wiring `--kind statusline` into Claude Code's real
`statusLine` command config -- whose stdout IS the rendered status text, a
fundamentally different contract than every other hook event -- is a
natural follow-up once that output-direction rendering exists, not part of
T90.

## Related Tasks

- T90 -- this hook + `gald3r_core.core.tel.host_adapter` (D001 ratified
  2026-07-13).
- T84-T87 -- the TEL engine (grammar/rules/decoration/ledgers/actions) this
  hook reuses wholesale, per g-rl-04.
- T424 -- the shared canonical event core (`g_hk_core.py`) this hook's two
  `CONCERN_CHAIN` registrations plug into.
