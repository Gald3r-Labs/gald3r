---
name: g-skl-browser-use
description: >
  Production browser harness for agentic web tasks requiring persistent sessions,
  stealth/anti-detect, CAPTCHA solving, and self-healing CDP code generation via
  the browser-use library (YC W25, $17M seed). Use for login-required sites,
  anti-bot environments, competitive intel, and long-running multi-step web tasks.
triggers:
  - browser-use
  - browser automation
  - production scraping
  - login-required
  - anti-bot
  - CAPTCHA
  - persistent session
  - stealth browser
  - competitive intel
  - cloud browser
  - BUX
token_budget: medium
subsystem_memberships: [AGENT_ORCHESTRATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
