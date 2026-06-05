---
skill_group: workflow:dev
skill_category: cursor-team-kit
---
# Control UI

Use local browser automation to verify UI behavior with evidence. First reuse the repo's own Playwright, browser, or Electron harness if it exists; otherwise assemble a temporary local harness around the app's dev server or Chromium debug port.

## What It Is Used For

- Reproducing UI bugs that depend on real browser focus, keyboard input, scrolling, resizing, or rendering.
- Verifying visual or accessibility changes with screenshots and snapshots.
- Checking local web, IDE, or Electron behavior before shipping.
- Capturing console logs, network logs, CPU profiles, traces, or heap snapshots.
- Creating before/after evidence for `verify-this`.

## Persistent Session Auth (Primary Pattern for Logged-In Tasks)

> **Rule:** If the task requires authentication, always use `connect_over_cdp` — it attaches to your existing Chrome session and inherits all cookies, tokens, and logged-in state. Never use `chromium.launch()` for auth-sensitive tasks — it starts a fresh browser with no sessions.

### Quick Start: auth-sensitive task

Start Chrome once with a persistent profile and debug port (do this manually or in a startup script):

```bash
# Windows
"<path-to-chrome>" --remote-debugging-port=9222 --user-data-dir=<AGENT_CHROME_PROFILE>
# macOS/Linux
google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-agent-profile
```

Connect from your agent (Python/Playwright):

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0]   # inherits all existing sessions
    page = context.pages[0]
    await page.goto("https://app.example.com/dashboard")
    await page.screenshot(path="/tmp/dashboard-logged-in.png", full_page=True)
```

Or in JavaScript:

```javascript
import { chromium } from "playwright";

const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
const context = browser.contexts()[0];  // inherits all existing sessions
const page = context.pages()[0];
await page.goto("https://app.example.com/dashboard");
await page.screenshot({ path: "/tmp/dashboard-logged-in.png", fullPage: true });
await browser.close();
```

### Why `--user-data-dir` matters

- The `--user-data-dir` flag points Chrome at a persistent profile directory.
- Cookies, local storage, and session tokens survive across agent restarts.
- Log in once in that Chrome profile — the agent inherits the session forever (until the session expires server-side).
- Use a dedicated agent profile (not your default profile) to avoid interfering with normal browsing.

### Verify login state before proceeding

Always confirm the session is valid before automation. A reliable pattern:

```python
# Confirm the authenticated element exists — bail early if session expired
await page.wait_for_selector("[data-testid='user-avatar'], .user-menu", timeout=5000)
```

If the selector is missing, the session has expired — surface a clear error rather than proceeding unauthenticated.

---

## Setup Pattern

1. Start the app locally using the repo's documented dev command.
2. Discover existing local harnesses: Playwright tests, Cypress specs, Storybook, browser scripts, Electron launch scripts, or snapshot tools.
3. **For auth-sensitive tasks:** Start Chrome with `--remote-debugging-port` + `--user-data-dir` and use `connectOverCDP` (see Persistent Session Auth above).
4. For a web app with no auth requirement, connect to the local URL with the existing browser tooling.
5. For Electron/Chromium, enable a remote debugging port when supported.
6. Select the correct page by stable app markers, not by tab order alone.
7. Prefer accessibility roles, labels, and stable `data-*` selectors over coordinates.

## Generic CDP Harness

For Electron or a Chromium app launched with `--remote-debugging-port=<port>`, connect over CDP:

```javascript
import { chromium } from "playwright";

const browser = await chromium.connectOverCDP("http://127.0.0.1:<debug-port>");
const pages = browser.contexts().flatMap((context) => context.pages());
let page;
for (const candidate of pages) {
  if (await candidate.locator("<app-root-selector>").count()) {
    page = candidate;
    break;
  }
}

if (!page) {
  console.log(await Promise.all(pages.map(async (p) => ({
    title: await p.title(),
    url: p.url(),
  }))));
  throw new Error("No matching app page found");
}

await page.screenshot({ path: "/tmp/ui-harness-cdp.png", fullPage: true });
await browser.close();
```

Replace `<app-root-selector>` with a stable marker from the current repo, such as a root app node, landmark, or product-specific `data-*` attribute.

## Interaction Loop

1. Capture a page snapshot or screenshot before acting.
2. Choose a target from the latest page structure.
3. Perform exactly one structural action: click, type, keypress, drag, scroll, navigate, or resize.
4. Capture a fresh snapshot/screenshot.
5. Verify the expected state change.
6. Save artifacts for before/after comparisons when the user asked for proof.

## CDP Capabilities

Use raw CDP only when higher-level browser APIs are insufficient:

- Performance: CPU profiles, traces, paint flashing, FPS meter, layout shift inspection.
- Memory: heap snapshots and forced GC for leak investigations.
- Network: request blocking, throttling, cache disablement, request/response logs.
- Rendering: viewport changes, color scheme emulation, reduced motion, accessibility checks.
- Debugging: console streaming, exception capture, DOM snapshots.

## Page Selection

When multiple app windows/tabs share a debug port:

- Prefer a positive marker for the surface under test, such as an app root selector.
- Use a negative marker to avoid the wrong surface when necessary.
- If no page matches, list available page titles and URLs instead of guessing.

## Guardrails

- Do not rely on stale element references after navigation or structural changes.
- Avoid coordinate clicks unless a fresh screenshot was captured immediately before the click.
- Keep test data local and disposable.
- Do not store screenshots or heap snapshots from privacy-sensitive workspaces unless the user explicitly agrees.
- Do not hard-code selectors, ports, or script paths from another repository. Discover the current repo's local app markers.
- Clean up dev servers, debug sessions, and temp profiles when done.

---

## Self-Healing Error Recovery

When a browser automation step fails — element not found, selector stale, interaction throws — do not immediately give up. Apply this 4-step recovery pattern before escalating.

### The 4-Step Recovery Pattern

**Step 1 — Detect and classify the failure**
```python
try:
    await page.click("[data-testid='login-btn']")
except Exception as e:
    failure_reason = str(e)
    # "Element not found", "Timeout waiting for selector", "Element is not visible"
```

**Step 2 — Read current page structure via accessibility snapshot**
```python
# Playwright accessibility snapshot
snapshot = await page.accessibility.snapshot()
# Or: get full DOM structure
html = await page.content()
# Or: take a screenshot for visual context
await page.screenshot(path="/tmp/failure-context.png", full_page=True)
```
Look for: the intended target (by text content, ARIA role, visible label), selector patterns visible in the current DOM, any dynamic ID patterns that replaced the expected static selector.

**Step 3 — Write a targeted helper function using raw CDP or page.evaluate()**
```python
# Write a helper that finds the element by content instead of fragile testid
recovery_helper = """
() => {
    // Find login button by text content (resilient to testid changes)
    const buttons = document.querySelectorAll('button, [role="button"], input[type="submit"]');
    const loginBtn = Array.from(buttons).find(el =>
        el.textContent.trim().toLowerCase().includes('sign in') ||
        el.textContent.trim().toLowerCase().includes('log in') ||
        el.value?.toLowerCase().includes('login')
    );
    if (loginBtn) {
        loginBtn.click();
        return { found: true, text: loginBtn.textContent.trim() };
    }
    return { found: false };
}
"""
result = await page.evaluate(recovery_helper)
```

**Step 4 — Patch into live session and retry**
```python
if result.get("found"):
    # Verify the action succeeded
    await page.wait_for_selector("[data-testid='dashboard'], .user-menu", timeout=5000)
    print(f"Recovery succeeded: clicked '{result['text']}'")
else:
    # Escalate: update the static selector or report the breaking change
    raise AutomationError(f"Recovery failed — page structure may have changed. Snapshot: {snapshot}")
```

### Worked Example: Dynamic `data-testid` That Changed Between Deploys

**Original automation (fragile):**
```python
await page.click("[data-testid='login-submit-btn']")
# Fails after deploy — testid changed to "auth-submit"
```

**Self-healing recovery:**
```python
try:
    await page.click("[data-testid='login-submit-btn']")
except:
    # Step 2: snapshot current structure
    snapshot = await page.accessibility.snapshot()

    # Step 3: write helper that finds by role + name
    result = await page.evaluate("""
    () => {
        const btn = document.querySelector('[data-testid*="submit"], [data-testid*="login"], button[type="submit"]');
        if (btn) { btn.click(); return { found: true, selector: btn.getAttribute('data-testid') }; }
        return { found: false };
    }
    """)

    # Step 4: patch — update the canonical selector for next run
    if result.get("found"):
        new_testid = result["selector"]
        print(f"⚠️ Selector drift detected: update test to use [{new_testid}]")
```

### Making Tests Resilient (vs Updating Fixed Selectors)

When to apply the self-healing pattern:
- Selector is `data-testid` or `id` that appears to have changed dynamically
- Element is present but interaction fails (wrong state, hidden, needs scroll)
- A/B test or feature flag changed the UI conditionally

When to update the fixed selector instead:
- The page was intentionally redesigned and the old selector no longer makes semantic sense
- A developer renamed a component and the new name is better/more stable
- The test is catching a real regression (the element genuinely disappeared — the test is correct)

### Claude Code Power Path

Claude Code can rewrite entire sections of the harness when a pattern has fundamentally changed:
- Give Claude the old test + a screenshot of current UI
- Prompt: "The selector `{old}` no longer works. Looking at this screenshot, what's the correct modern selector and interaction pattern?"
- Claude can update the entire test file, not just patch one line

This is Claude Code's native strength — use it when the self-healing 4-step pattern reveals a deeper structural change rather than a transient failure.
