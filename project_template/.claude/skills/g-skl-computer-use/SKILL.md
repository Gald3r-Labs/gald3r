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

# g-skl-computer-use — OS-Level Computer-Use Harness (T615)

**Triggers:** `computer use`, `desktop automation`, `GUI test`, `native app test`,
`drive the app`, `file-open dialog`, `throne UI test`, `screen control`, `pyautogui`

## When to Use This Skill

| Scenario | Use |
|---|---|
| Drive a **web page / dev-server** end-to-end | `g-skl-browser-use` (Playwright / CDP) |
| Login-required / anti-bot / cloud web tasks | `g-skl-browser-use` (BUX cloud) |
| **Drive a NATIVE desktop window (Throne, file dialogs, OS chrome)** | **`g-skl-computer-use` ← you are here** |
| **Open-ended "let a vision model figure out the screen"** | **`run_computer_use` runner (below)** |
| **Deterministic, scripted, pass/fail regression UI test in g-go** | **`UITestDriver` / `run_ui_test` (below)** |

**Key distinction from `g-skl-browser-use`:** browser-use only touches a browser
DOM. Computer-use drives the *whole operating system* — any window, the native
file-open dialog, the OS taskbar — at raw screen pixel coordinates. It is the
only path that can test a Tauri/Electron app's *native* shell (e.g. Throne's
native "open project" dialog, which is not reachable from the webview).

---

## What's Already Built (the pieces this skill wires together)

All of these live in `gald3r_agent/src/`:

1. **Five raw computer-use tools** — `src/tools/computer/`:
   `screenshot`, `click`, `type`, `scroll`, `key`. Each is a `ToolDefinition`
   with `permission="execute"` + `min_permission_mode="manual"` (deny-by-default,
   explicit approval). `pyautogui` + `pillow` are lazy-imported, so importing the
   harness never requires them and headless/CI installs never break.
2. **Vision-model loop** — `src/runners/computer_use_runner.py:run_computer_use`:
   the `screenshot → ask a multimodal model → action → repeat` loop. Use this
   for open-ended GUI tasks where the model decides each step.
3. **Deterministic UI-test driver (T615)** — `src/tools/computer/ui_test_driver.py`:
   `UITestDriver` + `run_ui_test()` + `throne_open_project_steps()`. A scripted,
   reproducible, **opt-in** path with a hard pass/fail verdict — the one g-go
   wires into its test/verify loop.

> This skill does NOT add a new tool framework. It documents and composes what
> already exists (g-rl-04 DRY).

---

## Installation

```bash
# From gald3r_agent/ — install the optional "computer" extra:
uv pip install -e ".[computer]"
# or, for the published wheel:
pip install "gald3r-agent[computer]"
```

This pulls `pyautogui>=0.9.54` and `pillow>=10.0`. Verify with the doctor:

```bash
gald3r doctor --check computer
```

It reports `pyautogui` import status, platform display access, and a
vision-model reminder. The check is always warn-or-pass (the extra is optional;
CI runs headless).

---

## Security & Opt-In Model (AC5 — scoped, opt-in, never unattended-by-default)

Computer-use drives the *real* mouse and keyboard. Three layers gate it:

1. **Per-tool permission gate (already in place).** Every raw tool is
   `permission="execute"` + `min_permission_mode="manual"`. The
   `computer_use` category is registered as **deny-by-default** in
   `src/permissions/classify.py`. `PermissionManager` prompts for an explicit
   session grant before any real input fires.
2. **Dual opt-in for the UI-test driver (T615).** `UITestDriver` / `run_ui_test`
   run **DRY by default** — they record the full plan but fire NO input. Live
   drive requires BOTH:
   - the caller passing `enable_live=True`, **and**
   - the environment variable `GALD3R_COMPUTER_USE_LIVE` set to a truthy value
     (`1` / `true` / `yes` / `on`).
   Either gate alone keeps it dry. This makes it impossible to seize the live
   machine by accident (e.g. a g-go run on a developer's desktop stays dry).
3. **Vision-model gate.** `run_computer_use` raises `ModelCapabilityError` if the
   active model is not multimodal, so it never loops blind.

> **Never run live computer-use unattended without an explicit, deliberate
> enablement.** The deterministic driver is dry-by-default precisely so it is
> safe to call from any pipeline; flip both opt-ins only on a machine you intend
> to hand over to the agent.

---

## Quick Start — Deterministic UI Test (the g-go path)

```python
from src.tools.computer import run_ui_test, region_is_non_blank

steps = [
    {"action": "screenshot"},
    {"action": "click", "x": 640, "y": 400},
    {"action": "type", "text": "hello"},
    {"action": "key", "keys": ["enter"]},
    {"action": "verify", "check": region_is_non_blank(), "region": [0, 0, 800, 600]},
]

# DRY by default — records the plan, fires nothing. status -> "skipped" (verify
# present) or "pass" (no verify). Safe to call in any pipeline / CI.
result = run_ui_test(steps)
print(result.status, result.summary)

# LIVE — requires BOTH the flag and the env var:
#   set GALD3R_COMPUTER_USE_LIVE=1   (PowerShell: $env:GALD3R_COMPUTER_USE_LIVE = "1")
result = run_ui_test(steps, enable_live=True)   # only goes live if env is also set
assert result.passed   # status == "pass"
```

`UITestResult.status` is `pass` / `fail` / `skipped`. `verify` steps supply a
`check(result) -> bool` callable that receives the screenshot `ToolResult`; use
`region_is_non_blank()` for a "something rendered" check, or hand
`result.output["image_base64"]` to a vision model for a real assertion.

---

## AC2 — Launch Throne + Drive the Native File-Open Dialog (BUILT, opt-in)

> **Status: BUILT-NOT-LIVE-VERIFIED.** The routine is implemented and unit-tested
> in dry mode, but driving it live needs a *built* Throne binary and an
> interactive desktop, and it seizes the real mouse/keyboard — so it is not run
> inside an agent worktree (T529 precedent). Run it deliberately on a desktop you
> hand to the agent.

```python
from src.tools.computer import run_ui_test, throne_open_project_steps, region_is_non_blank

# Build the canonical Windows-first flow as DATA (a step list):
steps = throne_open_project_steps(
    throne_binary=r"C:\Program Files\Gald3r Throne\Gald3r Throne.exe",
    project_path=r"C:\projects\demo",
    open_dialog_hotkey=["ctrl", "o"],      # override per Throne's real shortcut
    verify_check=region_is_non_blank(),    # or a vision-model "project loaded" check
)

# Dry-run first to inspect the plan (fires nothing):
print(run_ui_test(steps).summary)

# Live (deliberate): set GALD3R_COMPUTER_USE_LIVE=1, then:
result = run_ui_test(steps, enable_live=True)
assert result.passed
```

The flow: launch → screenshot → `Ctrl+O` (open dialog) → wait → type the project
path into the dialog's filename field → `Enter` → wait for load → verify. Adjust
the hotkey and coordinates to Throne's actual UI before live use.

---

## AC3 — g-go Test/Verify Loop Integration (seam)

`run_ui_test(steps) -> UITestResult` is the **stable callable entrypoint** the
g-go test/verify loop wires into. It is dry-by-default and returns a structured
`pass`/`fail`/`skipped` verdict, so a verify step can gate a task:

```python
from src.tools.computer import run_ui_test

def gold_ui_check() -> bool:
    result = run_ui_test(MY_UI_STEPS, enable_live=True)
    return result.passed    # FAIL the task if the UI flow did not pass live
```

Live-loop wiring (calling this from the actual g-go-review step on an enabled
host) is a documented follow-up — see the FOLLOW-UP note in the task handoff.
The seam is in place; nothing in the loop runs live until `GALD3R_COMPUTER_USE_LIVE`
is set on the host.

---

## AC4 — Cross-Platform Notes (Windows first)

| Platform | Status | Notes |
|---|---|---|
| **Windows 10/11** | Primary / first | `pyautogui` works natively; `gald3r doctor --check computer` reports `pyautogui.size()`. This is the validated path. |
| **macOS** | Supported | Grant the controlling process **Accessibility** permission (System Settings → Privacy & Security → Accessibility) or input is silently dropped. |
| **Linux (X11)** | Supported | Requires `$DISPLAY`; install `python3-tk`/`scrot` for screenshots. |
| **Linux (Wayland)** | Limited | `pyautogui` (XTEST) is unreliable under Wayland; use an X11 session or a VNC bridge. |
| **Headless / CI / containers** | Use a **VNC bridge** | Run a virtual display (`Xvfb` + `x11vnc`, or a `vnc`-enabled container) and point the agent's display at it. This isolates the live mouse/keyboard from any real operator and is the recommended way to run *live* computer-use unattended-but-safe. |

**VNC bridge sketch (Linux/CI):** start `Xvfb :99` → `x11vnc -display :99` →
export `DISPLAY=:99` for the agent process → run the live UI test against the
virtual display. The operator's real desktop is never touched.

---

## Parity / Follow-Ups

- This SKILL.md lives under `.claude/skills/` which is gitignored personal IDE
  config; it is NOT committed by the implementing agent. **Coordinator
  follow-up:** run `platform_parity_sync.ps1 -Sync` to propagate it to the other
  IDE targets (`.cursor/`, `.codex/`, `.agent/`, `.opencode/`) and into the
  shipped templates.
- **Follow-up:** wire `run_ui_test` into the live g-go-review step behind a host
  capability check (`GALD3R_COMPUTER_USE_LIVE` + a built Throne binary).
- **Follow-up:** add a vision-model `verify` check helper that asserts a named
  element is visible (beyond the `region_is_non_blank` baseline).

## Quick Reference

| Operation | Code |
|---|---|
| Dry-run a scripted UI test | `run_ui_test(steps)` |
| Live UI test (both opt-ins) | `GALD3R_COMPUTER_USE_LIVE=1` + `run_ui_test(steps, enable_live=True)` |
| Build the Throne open-project flow | `throne_open_project_steps(binary, project_path)` |
| Baseline "rendered" verify check | `region_is_non_blank()` |
| Open-ended vision-model loop | `run_computer_use(task, backend)` |
| Doctor check | `gald3r doctor --check computer` |

**Source:** `gald3r_agent/src/tools/computer/ui_test_driver.py`,
`gald3r_agent/src/tools/computer/`, `gald3r_agent/src/runners/computer_use_runner.py`
