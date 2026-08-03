# g-go-go Companion: Full Usage Examples

> Extracted verbatim from `commands/g-go-go.md` under T588 (file-size decomposition,
> repo threshold g-rl-00) -- content unchanged, relocated only. Companion:
> `commands/g-go-go.md` (the base command spec -- see its "Usage Examples" section for
> a short curated subset and a pointer back here for the complete list).

## Usage Examples

```
@g-go-go
@g-go-go --budget 5
@g-go-go --heartbeat 15m
@g-go-go --controller-only
@g-go-go --controller-only --budget 3
@g-go-go tasks 220, 222, 223
@g-go-go bugs-only
@g-go-go subsystem multiple-ide-platform-parity
@g-go-go --target-branch main           # default: PASS items merge to main (feature-branches-only model)
@g-go-go --no-auto-merge                # disable auto-merge; reviewer leaves [MERGE-BLOCKED] for human
@g-go-go --target-branch staging        # merge to a custom branch instead of main
@g-go-go --repos example_agent --budget 3   # scope autopilot to example_agent tasks only
@g-go-go --repos example_agent,example_desktop # scope autopilot to two specific member repos
@g-go-go --reset-every 3                 # [--legacy only] Rolling Amnesia cadence (deprecated; inert under the default conductor)
@g-go-go --reset-every 6                 # less frequent context resets (longer-lived coordinator sessions)
@g-go-go --no-reset                      # disable Rolling Amnesia; use the legacy iteration-count throttle
@g-go-go --resume .gald3r/logs/ggo_run_state.json  # resume after a scheduled reset (normally issued by the hook)
@g-go-go                                 # DEFAULT: T630 stateless conductor (gald3r autopilot loop), fresh coordinator per iteration
@g-go-go --stateless --budget 8          # stateless run, 8-iteration budget
@g-go-go --legacy                        # force the DEPRECATED single-session loop (was the old default)
@g-go-go --subsystem MEMORY_AND_KNOWLEDGE  # T632: scope this coordinator to one subsystem (Pro+)
@g-go-go --subsystem UI_AND_OUTPUT         # a second, disjoint-scope coordinator may run in parallel
@g-go-go --no-context-aware              # disable context-aware throttle (full N at all context levels)
@g-go-go --no-context-aware --budget 3  # short burst: max parallelism, no throttle
@g-go-go --no-code-swarm                 # Phase 1 sequential coding (1 task at a time); Phase 2 review swarm unchanged
@g-go-go --no-code-swarm --budget 3      # safe debugging mode: sequential coding, parallel review
```
