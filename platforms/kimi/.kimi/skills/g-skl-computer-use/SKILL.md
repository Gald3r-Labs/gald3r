---
name: g-skl-computer-use
description: >
  OS-level computer-use harness for Gald3r — capture the screen and issue
  mouse/keyboard input at OS coordinates to drive ANY native desktop app
  (not just a browser) end-to-end without a human. Built on the five existing
  computer-use tools (screenshot/click/type/scroll/key) plus a deterministic,
  opt-in UI-test driver. Use for autonomous GUI testing of the Throne desktop
  app and any native-window verification the g-go loop needs.
triggers:
  - computer use
  - computer-use
  - desktop automation
  - GUI test
  - native app test
  - drive the app
  - file-open dialog
  - throne UI test
  - screen control
  - mouse keyboard control
  - pyautogui
token_budget: medium
subsystem_memberships: [AGENT_ORCHESTRATION, PLATFORM_INTEGRATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Run: `gald3r ui-test run`
Documentation: https://docs.gald3r.ai
