# Next Release - gald3r

**Status:** Draft - version number assigned at publish time.

Use this file for **promotional, enticing** copy that will headline the next GitHub release.
Technical detail belongs in [CHANGELOG.md](../CHANGELOG.md). User-facing how-to belongs in the
[README.md](../README.md) pending section.

---

## Headline

Autopilot that knows when to stop, and updates that can't eat your project.

---

## What's coming

- **Your budget is safe.** `@g-go-go` now halts the moment a coordinator hits an account-level
  wall (monthly spend cap, low credit balance, bad/expired key) instead of silently re-spawning
  failing sessions until the budget is gone. A consecutive-failure circuit breaker backs it up,
  and the run state always records *why* it stopped.
- **Self-update can no longer wipe your work.** `gald3r update` now only ADDs and MERGEs by
  default — it never deprecates your authored content, and it takes a full timestamped backup of
  every framework tree before it touches anything. Deprecation is strictly opt-in.
- **You can finally see it working.** The autopilot conductor streams live, timestamped progress
  to the terminal and log, so a long-running task no longer looks dead while it's hard at work.
- **No more clobbered release notes.** Publishing detects an unfilled notes template and falls
  back to the changelog, so empty promo skeletons can't ship as your release page again.
- **Safer concurrent task/bug creation.** During multi-agent runs, new tasks and bugs route
  through the hot inbox so parallel agents can't collide on the same ID.
- **The maintainer pipeline is Python.** The deploy step joins build and publish as a tested
  Python system, and the release scripts are renumbered by run order.

---

## Why upgrade now

If you run gald3r autopilot, 2.2.0 is the release that protects your wallet and your data: runs
stop on fatal account errors instead of grinding to zero, and updates back themselves up before
making a single change.

---

_See [CHANGELOG.md](../CHANGELOG.md) for the full technical list._
