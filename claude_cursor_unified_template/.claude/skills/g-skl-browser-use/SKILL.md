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

# g-skl-browser-use — Production Browser Harness

**Triggers:** `browser-use`, `browser automation`, `production scraping`, `login-required`,
`anti-bot`, `CAPTCHA`, `persistent session`, `stealth browser`, `competitive intel`, `BUX`

## When to Use This Skill

| Scenario | Use |
|---|---|
| Dev/test automation with stable selectors | `ui-control` |
| IDE-driven UI verification and screenshots | `ui-control` + `cursor-ide-browser` MCP |
| Local Playwright/Cypress test harness | `ui-control` |
| **Login-required site (inherit existing session)** | **`g-skl-browser-use` ← you are here** |
| **Sites with CAPTCHA or bot detection** | **`g-skl-browser-use` (cloud tier)** |
| **Production monitoring and competitive intel** | **`g-skl-browser-use`** |
| **Long-running agentic web tasks (async, multi-step)** | **`g-skl-browser-use`** |
| **Self-healing: agent writes its own missing helpers** | **`g-skl-browser-use`** |

**Key distinction:** `ui-control` is a dev/test harness you write and maintain.
`browser-use` is an AI-driven engine that writes, repairs, and re-executes its own
browser code autonomously — designed for production tasks the agent must complete
without human selector maintenance.

---

## Installation

```bash
pip install browser-use
# Playwright browsers (first time only)
playwright install chromium
```

For cloud tier (BUX), no local installation is needed — connect via CDP URL.

---

## Auth Pattern: Persistent Chrome Profile

> **Rule:** For any login-required site, always attach to an existing Chrome session via
> `connect_over_cdp`. Never use a fresh `chromium.launch()` — it starts with no cookies
> and will hit login walls immediately.

### 1. Start Chrome once with a persistent profile

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir=C:\Users\You\chrome-agent-profile

# macOS / Linux
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=$HOME/.chrome-agent-profile
```

Log into every target site manually in this profile. The agent will inherit all
cookies, local storage tokens, and session state on every subsequent run.

### 2. Attach browser-use to the running session

```python
import asyncio
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig

async def run():
    browser = Browser(
        config=BrowserConfig(
            # Attach to the persistent profile already running on port 9222
            cdp_url="http://localhost:9222",
        )
    )
    agent = Agent(
        task="Navigate to https://app.example.com/dashboard and capture the pricing table",
        browser=browser,
    )
    result = await agent.run()
    print(result)

asyncio.run(run())
```

### Why `--user-data-dir` matters

- Cookies, local storage, and tokens persist across agent restarts.
- Log in once — the agent inherits the session until it expires server-side.
- Use a dedicated agent profile, not your default Chrome profile, to prevent
  interference with normal browsing.
- Store the profile path in an env var: `AGENT_CHROME_PROFILE=C:\Users\You\chrome-agent-profile`

### Verify session before proceeding

```python
page = await browser.get_current_page()
try:
    await page.wait_for_selector("[data-testid='user-avatar'], .user-menu", timeout=5000)
except Exception:
    raise RuntimeError("Session expired — re-authenticate in the agent Chrome profile")
```

---

## Self-Healing Pattern

browser-use generates CDP/Playwright helper code on the fly. When a helper function
is missing or a selector breaks, the agent:

1. Reads its own generated helper file.
2. Writes the missing or corrected function.
3. Patches the live browser session via CDP execution.
4. Retries the failed action automatically.

### Enable self-healing

```python
from browser_use import Agent
from browser_use.agent.service import AgentConfig

agent = Agent(
    task="...",
    config=AgentConfig(
        # Allow agent to write and execute new helper code
        enable_self_healing=True,
        helper_file_path=".cache/browser_use_helpers.py",
    ),
)
```

### Manual self-heal pattern (when automatic is disabled)

```python
import importlib.util, pathlib

HELPER_FILE = pathlib.Path(".cache/browser_use_helpers.py")

async def self_heal(agent, missing_fn_name: str, fn_source: str):
    """Write a missing helper, reload it, and patch into the live session."""
    HELPER_FILE.write_text(fn_source)
    spec = importlib.util.spec_from_file_location("helpers", HELPER_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Inject into agent's live context
    agent.browser_context.helpers = mod
    # CDP: execute a quick smoke-test to confirm the patch loaded
    page = await agent.browser.get_current_page()
    await page.evaluate(f"() => typeof window.{missing_fn_name} !== 'undefined'")
```

---

## Cloud Tier (BUX — Browser Use Box)

BUX is browser-use's managed cloud, providing:
- **Persistent Chrome profiles** stored in cloud (no local Chrome needed)
- **195-country residential proxies** for geo-fencing or IP-block bypass
- **Automatic CAPTCHA solving** (reCAPTCHA v2/v3, hCaptcha, Cloudflare Turnstile)
- **Stealth fingerprinting** (User-Agent rotation, WebGL noise, Canvas hash spoofing)
- **Free tier:** unlimited browser hours (as of 2026-Q2)

### Connect to BUX cloud browser

```python
import os
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig

async def run():
    browser = Browser(
        config=BrowserConfig(
            # BUX provides a per-session WebSocket CDP URL
            cdp_url=os.environ["BUX_CDP_URL"],   # e.g. wss://bux.browser-use.com/session/abc123
        )
    )
    agent = Agent(
        task="Monitor competitor pricing page and extract the pricing table",
        browser=browser,
    )
    return await agent.run()
```

Set `BUX_CDP_URL` in your `.env` or vault env block. Rotate to a new session URL
after each logical task boundary (BUX sessions are stateless across URLs by default
unless you pass `persistent_profile=True` in the BUX session-create API call).

### BUX session lifecycle

```python
import httpx, os

async def create_bux_session(country: str = "US", persistent: bool = True) -> str:
    resp = httpx.post(
        "https://api.browser-use.com/v1/sessions",
        headers={"Authorization": f"Bearer {os.environ['BUX_API_KEY']}"},
        json={"country": country, "persistent_profile": persistent},
    )
    resp.raise_for_status()
    return resp.json()["cdp_url"]
```

---

## Security Warnings

> **This skill involves persistent, self-modifying browser automation.
> Follow every item below before running in production.**

1. **Scope permissions explicitly.** Use `AllowedDomains` to restrict what URLs
   the agent can navigate to. Never pass an unbounded task like "search the web."

   ```python
   from browser_use.agent.service import AgentConfig
   config = AgentConfig(allowed_domains=["competitor.com", "pricing.competitor.com"])
   ```

2. **Never pass raw credentials to the agent task string.** Use the persistent
   profile pattern (above) so the agent inherits sessions — it never sees your password.

3. **Sandbox the helper file path.** `enable_self_healing` writes and executes Python
   on your machine. Restrict the helper file to a `.cache/` directory that is gitignored.

   ```gitignore
   .cache/browser_use_helpers.py
   .cache/bux_sessions/
   ```

4. **gald3r permission hook integration.** Before running any browser-use agent in a
   gald3r workflow, call the permission gate hook:

   ```powershell
   # Pre-flight gate — blocks if the target URL is outside the approved domain list
   powershell -NoProfile -File .cursor/hooks/g-hk-browser-permission-check.ps1 `
     -TargetUrl $env:TASK_TARGET_URL `
     -AllowedDomains $env:BROWSER_ALLOWED_DOMAINS
   ```

   If `g-hk-browser-permission-check.ps1` does not yet exist in your project, add
   a task to create it before using this skill in automated pipelines.

5. **Rate limiting.** Add random delays between page actions to avoid triggering
   velocity-based bot detection even when using BUX stealth:

   ```python
   import random, asyncio
   await asyncio.sleep(random.uniform(1.5, 4.0))
   ```

6. **Terms of Service compliance.** Automated access to competitor sites may violate
   their ToS. Obtain legal sign-off before deploying production competitive intel scrapers.

---

## Worked Example: Competitor Pricing Monitor

**Task:** Agent logs into a SaaS competitor's pricing page (login-required, anti-bot
protected), extracts the current pricing table, compares it to the last known snapshot
in the vault, and writes a diff note to `research/competitive/`.

```python
import asyncio, json, os, pathlib
from datetime import date
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig

VAULT = pathlib.Path(os.environ.get("VAULT_PATH", "vault"))
OUT_DIR = VAULT / "research" / "competitive"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_FILE = OUT_DIR / "competitor_pricing_latest.json"

async def monitor_competitor_pricing():
    browser = Browser(
        config=BrowserConfig(
            # BUX cloud: stealth + CAPTCHA solving + residential proxy
            cdp_url=os.environ["BUX_CDP_URL"],
        )
    )

    task = """
    1. Navigate to https://competitor.com/pricing (already logged in via persistent profile).
    2. Wait for the pricing table to fully load — look for elements with class
       'pricing-card' or 'plan-price'.
    3. Extract each plan: name, monthly price, annual price, and feature list.
    4. Return the data as a JSON array of objects with keys:
       plan_name, monthly_usd, annual_usd, features (list of strings).
    5. If you encounter a CAPTCHA, solve it and retry.
    6. If the pricing page requires login, report "SESSION_EXPIRED" as the result.
    """

    agent = Agent(task=task, browser=browser)
    raw = await agent.run()

    # Parse the structured output
    try:
        current = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(f"Agent returned non-JSON: {raw[:200]}")

    # Compare to last snapshot
    previous = json.loads(SNAPSHOT_FILE.read_text()) if SNAPSHOT_FILE.exists() else []
    diff = compute_pricing_diff(previous, current)

    # Write vault note
    today = date.today().isoformat()
    vault_note = OUT_DIR / f"{today}_competitor_pricing_snapshot.md"
    vault_note.write_text(f"""---
date: {today}
type: competitive_intel
source: https://competitor.com/pricing
title: Competitor Pricing Snapshot {today}
topics: [pricing, competitive-intel, browser-use]
---

# Competitor Pricing — {today}

## Changes Since Last Snapshot

{diff if diff else "_No changes detected._"}

## Current Pricing

```json
{json.dumps(current, indent=2)}
```
""")

    # Update snapshot
    SNAPSHOT_FILE.write_text(json.dumps(current, indent=2))
    print(f"[browser-use] Snapshot written to {vault_note}")
    return current


def compute_pricing_diff(prev: list, curr: list) -> str:
    prev_map = {p["plan_name"]: p for p in prev}
    curr_map = {p["plan_name"]: p for p in curr}
    lines = []
    for name, data in curr_map.items():
        if name not in prev_map:
            lines.append(f"- **NEW plan:** {name} — ${data['monthly_usd']}/mo")
        elif data["monthly_usd"] != prev_map[name]["monthly_usd"]:
            lines.append(
                f"- **Price change:** {name} "
                f"${prev_map[name]['monthly_usd']} → ${data['monthly_usd']}/mo"
            )
    for name in prev_map:
        if name not in curr_map:
            lines.append(f"- **REMOVED plan:** {name}")
    return "\n".join(lines)


if __name__ == "__main__":
    asyncio.run(monitor_competitor_pricing())
```

Run this as a scheduled gald3r task or trigger it via a `@g-recon-url` hook.

---

## Quick Reference

| Operation | Code |
|---|---|
| Local CDP attach | `BrowserConfig(cdp_url="http://localhost:9222")` |
| BUX cloud attach | `BrowserConfig(cdp_url=os.environ["BUX_CDP_URL"])` |
| Enable self-healing | `AgentConfig(enable_self_healing=True)` |
| Restrict allowed domains | `AgentConfig(allowed_domains=["example.com"])` |
| Add stealth delay | `await asyncio.sleep(random.uniform(1.5, 4.0))` |

**Docs:** https://github.com/browser-use/browser-use
**Cloud:** https://browser-use.com (BUX free tier)
