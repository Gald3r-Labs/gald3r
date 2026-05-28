---
name: g-skl-platform-cursor
description: Authoritative reference for Cursor IDE customization in gald3r projects. Covers .cursor/ folder layout, all supported primitives (rules/skills/agents/commands/hooks/MCP), parity tiers, vault doc location, crawl freshness gate, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/cursor/
vault_docs_url: https://docs.cursor.com
docs_url: https://docs.cursor.com
last_doc_scan: never
reference_implementation: true
capability_status:
  hooks: "✅ native hooks.json (sessionStart/stop/beforeShellExecution/preToolUse) — verified"
  rules: "✅ .mdc always-apply + glob-scoped — verified"
  skills: "✅ folder-per-skill auto-load — verified"
  commands: "✅ @g-* command markdown — verified"
  mcp: "✅ mechanism (.cursor/mcp.json / settings) — server set per-machine, untested in CI"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-cursor

Activate for: setting up Cursor in a gald3r project, authoring rules/skills/agents/commands/hooks, understanding .cursor/ structure, verifying Cursor parity, or answering questions about Cursor's capabilities.

---

## Crawl Freshness Gate

```
1. Read {vault_location}/.crawl_schedule.json
2. Find entry for: https://docs.cursor.com
3. If entry missing OR (today - last_crawl) > 7 days:
   → TRIGGER g-skl-recon-docs with URL https://docs.cursor.com
   → READ new vault notes at research/platforms/cursor/
   → UPDATE sections: "Platform Overview", "Supported Primitives", "Common Pitfalls"
4. Else: proceed with current content
```

**Self-Update Procedure**: After a fresh crawl, update sections 1, 3, and 9 of this SKILL.md using StrReplace on the changed content.

---

## 1. Platform Overview

**Cursor** is an AI-first IDE built on VS Code, with deep agent mode integration. It runs locally as a desktop application.

- **Agent mode**: Background agents that autonomously complete multi-step tasks
- **Inline completions**: Tab-to-accept AI suggestions
- **Chat**: Sidebar chat with @ references to files, symbols, docs, and skills
- **Rules**: Auto-applied context injected into every session
- **Skills**: On-demand specialist procedures (`.cursor/rules/` or SKILL.md files)
- **MCP**: MCP servers accessible via Cursor's settings or `.cursor/mcp.json`

**gald3r target tier**: Canonical source. All gald3r features originate in `.cursor/` and propagate to other platforms.

---

## 2. Folder Layout

```
.cursor/
├── rules/                    ← Always-apply rules (.mdc format, loaded every session)
│   └── g-rl-*.mdc            ← Numbered rules (00-always, 01-docs, 25-session-start, etc.)
├── skills/                   ← Agent skills (auto-discovered by Cursor)
│   └── g-skl-*/SKILL.md      ← Each skill in its own folder
├── agents/                   ← Specialist agent definitions (markdown)
│   └── g-agnt-*.md
├── commands/                 ← @g-* slash commands (referenced via @ in chat)
│   └── g-*.md
├── hooks/                    ← PowerShell automation hooks + T1171 companion .md files
│   ├── g-hk-*.ps1
│   └── g-hk-*.md             ← companion hook docs (one per .ps1)
├── hooks.json                ← native hook wiring at .cursor/hooks.json (TOP-LEVEL, not in hooks/)
└── mcp.json                  ← MCP server config (optional; or in Cursor settings / root .mcp.json)
```

**Key**: `.mdc` extension is Cursor-specific for rules. Other platforms use `.md`.

---

## 3. Supported Primitives

| Primitive | Location | Format | Auto-loaded? |
|---|---|---|---|
| Always-apply rules | `.cursor/rules/g-rl-*.mdc` | Markdown + frontmatter | ✅ Every session |
| Skills | `.cursor/skills/<name>/SKILL.md` | Markdown + frontmatter | ✅ When relevant |
| Agents | `.cursor/agents/g-agnt-*.md` | Markdown | Manual select |
| Commands | `.cursor/commands/g-*.md` | Markdown | Via `@command-name` |
| MCP servers | `.cursor/mcp.json` or Cursor settings | JSON | ✅ Auto-connect |
| Hooks | Native wiring at `.cursor/hooks.json` (sessionStart/stop/beforeShellExecution/preToolUse) → PS1 scripts in `.cursor/hooks/` | hooks.json + PS1 | ✅ On matching event |

---

## 3a. Hook capabilities (T600)

T600 / `feat-106` extends gald3r's hook layer with four contract-level features harvested from OpenHarness, plus a 6-event worktree lifecycle. **Design-of-record:** [`docs/20260506_000000_Cursor_T600_HOOK_SYSTEM_EXTENSIONS.md`](../../../docs/20260506_000000_Cursor_T600_HOOK_SYSTEM_EXTENSIONS.md).

| Feature | What it adds | Reference |
|---|---|---|
| **HTTP hook type (B-2)** | `hooks.json` entries with `"type": "http"`, `"url"`, `"allow_hosts"`, `"timeout_ms"`, `"auth_header_env"`. Reference caller: `.claude/hooks/g-hk-http-event.ps1` (parity-propagation to `.cursor/hooks/` is a follow-up). | Design doc §1 |
| **Glob tool matcher (B-3)** | `pre_tool_use` / `post_tool_use` entries gain `"tool_match": ["bash_*", "file_*"]`. Helper: `Test-HookToolMatch` in `.gald3r_sys/scripts/gald3r_hook_helpers.ps1`. | Design doc §2 |
| **`block_on_failure` (B-4)** | Hook entries gain `"block_on_failure": true` to abort the triggering operation on failure. Override: `$env:GALD3R_HOOK_BYPASS=1`. | Design doc §3 |
| **Shell-safe arg substitution (B-6)** | `Convert-HookArgSafe -Value $x -Shell powershell\|bash` in `.gald3r_sys/scripts/gald3r_hook_helpers.ps1` produces single-quoted literals safe for command substitution. | Design doc §4 |

### 6-event worktree lifecycle (D-6)

`scripts/gald3r_worktree.ps1 -Action Event -Event <name>` fires per-worktree hooks at the canonical 6 lifecycle points: `claim`, `pre-impl`, `post-impl`, `pre-review`, `post-review`, `cleanup`. Hook scripts live at `<worktree>/.gald3r-worktree-hooks/<event>.ps1` (worktree-local) and/or `.gald3r/hooks/worktree/<event>.ps1` (repo-wide). Both fire if both exist; failure honors `-BlockOnFailure`.

Lifecycle stamps are written to each worktree's `.gald3r-worktree.json` under a new `lifecycle:` map keyed by event name (and `<event>_<bucket>` in swarm flows).

### gald3r-internal lifecycle events (T1055)

Beyond the harness-native events (`sessionStart`, `stop`, `beforeShellExecution`, `preToolUse`), gald3r defines four **gald3r-internal** lifecycle events. Cursor does NOT expose a native skill-boundary event nor a gald3r-session-boundary event, so these are dispatched by the gald3r skill/command runner (or fired manually) and are **NOT auto-wired** into `.cursor/hooks.json` — like `manual` and `nightly` hooks. They enable per-skill tracing/timing and per-session observability without editing skill bodies.

| Event | Payload (stdin JSON) | Fires |
|-------|----------------------|-------|
| `pre_skill` | `skill_name`, `skill_path`, `timestamp` | Before a skill body executes |
| `post_skill` | `skill_name`, `skill_path`, `timestamp` | After a skill body finishes |
| `pre_session` | `session_id` (if available), `project_path` | Session start (gald3r-level, not harness `sessionStart`) |
| `post_session` | `session_id` (if available), `project_path` | Session end (gald3r-level, not harness `stop`) |

Reference example hooks (under `.cursor/hooks/`, each with a companion `hook.md`): `g-hk-pre-skill-timing.ps1` + `g-hk-post-skill-timing.ps1` (per-skill elapsed timing via a `.gald3r/logs/skill_timing_*.json` start marker), and `g-hk-pre-session-trace.ps1` + `g-hk-post-session-trace.ps1` (per-session duration via `.gald3r/logs/session_trace_*.json`). All four are non-blocking, emit the standard `{ continue = true }` envelope, and never touch control-plane state. The `_doc.gald3r_lifecycle_events` key in `hooks.json` documents the same contract. Scaffold new ones with `@g-hook-create <hook-name> pre_skill|post_skill|pre_session|post_session`.

### Reference helpers

- `.gald3r_sys/scripts/gald3r_hook_helpers.ps1` — `Test-HookToolMatch`, `Convert-HookArgSafe`, `Read-HookEventEnvelope`. Run with `-RunSelfTest` to verify behavior.
- `.claude/hooks/g-hk-http-event.ps1` — drop-in HTTP hook caller (host allow-list, HTTPS-for-non-loopback, timeout cap, bearer auth via env var). Cursor parity copy is a deferred follow-up.
- `.cursor/hooks/g-hk-pre-commit.ps1` — already speaks BLOCK/WARN via exit codes; will honor `$env:GALD3R_HOOK_BYPASS=1` once the T600 patch is propagated from `.claude/hooks/`.

---

## 4. gald3r Parity Tier

Cursor is the **canonical source** for gald3r. All content originates here.

| Content | Slim | Full | Adv |
|---|---|---|---|
| rules/ (8 always-apply) | ✅ | ✅ | ✅ |
| skills/ (core gald3r) | ✅ | ✅ | ✅ |
| agents/ | ✅ | ✅ | ✅ |
| commands/ | ✅ | ✅ | ✅ |
| hooks/ | ✅ | ✅ | ✅ |

Run `.\custom_scripts\platform_parity_sync.ps1` to propagate changes to all 11 other targets.

---

## 4a. Common vs. Platform-Specific Decision Tree (T1460 — reference)

This is the canonical decision rule for **where any new capability goes** across the 23
gald3r platforms. `g-agnt-platformer` and `g-skl-platform-monitor` defer to it.

### Common (all platforms inherit)
Lives in `.gald3r_sys/skills/`, `.gald3r_sys/agents/`, `.gald3r_sys/hooks/`, `.gald3r_sys/rules/`.
Propagated to every platform via `platform_parity_sync.ps1`:
- All `g-skl-*` skills (universal gald3r logic)
- All `g-agnt-*` agents (universal orchestration)
- Framework rules (`.gald3r_sys/rules/`)
- Core hooks (session-start, session-end, medic hooks)

### Platform-Specific (per-platform overrides)
Lives in `.gald3r_sys/platforms/.<platform>/` — only deployed to that platform:
- `hooks.json` / `settings.json` — hook wiring format varies per platform
- Platform SDK skills (e.g., `.claude/agents/sdk/`, `.cursor/agents/sdk/`)
- Platform-native rule format (Cursor `.mdc` vs. Claude `.md`)
- Platform-specific MCP server config
- Platform-native command format

### The decision tree (for new capabilities)
```
Is this gald3r logic that ALL platforms should have?
  YES → Add to .gald3r_sys/skills/ or .gald3r_sys/hooks/ (common)
  NO  → Does the platform have a native equivalent concept?
    YES → Add platform-specific config to .gald3r_sys/platforms/.<platform>/
    NO  → Document the gap in g-skl-platform-<platform>/SKILL.md under "Known Gaps"
```

A capability is therefore always one of: (a) common, (b) platform-specific override, or
(c) a documented gap. `g-skl-platform-monitor VALIDATE` flags platform override dirs whose
contents are byte-identical to the Cursor copy (i.e. "Cursor-generic", not genuinely platform-specific).

---

## 5. Vault Doc Location

```
{vault_location}/research/platforms/cursor/
```

Crawl entry point: `https://docs.cursor.com`

---

## 6. Crawl Freshness Gate (Detail)

`.crawl_schedule.json` entry:
```json
{
  "https://docs.cursor.com": {
    "last_crawl": "YYYY-MM-DD",
    "vault_path": "research/platforms/cursor/",
    "max_age_days": 7
  }
}
```

---

## 7. Self-Update Procedure

After each fresh crawl: read `research/platforms/cursor/*.md`, update sections 1, 3, and 9 with any changed capabilities or file paths.

---

## 8. Key URLs

| Purpose | URL |
|---|---|
| Cursor docs (primary) | https://docs.cursor.com |
| Rules documentation | https://docs.cursor.com/context/rules |
| MCP documentation | https://docs.cursor.com/context/model-context-protocol |
| Agent mode | https://docs.cursor.com/agent |

---

## 9. Common Pitfalls

1. **Rules must use `.mdc` extension** — Cursor only auto-loads rules with `.mdc`. Other platforms use `.md`. The parity sync handles extension mapping automatically.
2. **Skills folder structure** — Each skill must be in its own subfolder: `.cursor/skills/my-skill/SKILL.md`. A loose `.md` file in `skills/` root is NOT picked up.
3. **Canonical framework source** — Edit `gald3r_templates/gald3r_template/.gald3r_sys/` (and `gald3r_templates/.cursor/` for maintainer IDE trees), then run `gald3r_templates/custom_scripts/platform_parity_sync.ps1 -SyncGaldSys -Sync`. Do not hand-edit `gald3r_dev/.gald3r_sys/` or tier `gald3r_template_*/gald3r_template/` copies.
4. **MCP timeout** — Default Cursor MCP timeout is 60s. For long-running tools, set `mcp.server.timeout: 600000` in Cursor settings.json.
5. **Proprietary skills stay in `.cursor/` only** — Never propagate business-specific or proprietary skills to `G:/gald3r_ecosystem/gald3r_template_full`. C-009 exemption applies.

---

## 9a. Reference Implementation Status (T1461)

**Cursor is the gald3r reference platform.** All primitives originate in the `.cursor/` tree and
propagate to the other 22 platforms via `custom_scripts/platform_parity_sync.ps1`. The companion
[`PLATFORM_SPEC.md`](./PLATFORM_SPEC.md) in this skill folder is the **gold standard** every other
platform's `PLATFORM_SPEC.md` (T1462–T1483) is compared against.

Verified capability (see PLATFORM_SPEC.md §10 Verification Evidence):

| Capability | Status | Evidence |
|---|---|---|
| Hooks | ✅ | native `.cursor/hooks.json`, 4 events wired |
| Rules | ✅ | 17 `g-rl-*.mdc` always-apply / glob-scoped |
| Skills | ✅ | 110 folder-per-skill `SKILL.md` |
| Commands | ✅ | 174 `@g-*` command markdown files |
| MCP | ✅ | mechanism verified; server set per-machine |
| Docs freshness | ❓ | `last_doc_scan: never` — pending SCAN_DOCS |

**Overall cursor platform score: ≥95%** (the single open item is docs-freshness verification via
`@g-platform-scan-docs cursor`, not a capability gap).

## 9b. Known Gaps

Cursor is the reference, so there are no "gaps vs. another platform." These are the
incomplete/deferred/unverified items within the Cursor implementation itself (the honest baseline
that feeds `PLATFORM_STATUS.md` — full detail in PLATFORM_SPEC.md §9):

1. **T600 HTTP hook parity** — `g-hk-http-event.ps1` lives in `.claude/hooks/`; `.cursor/hooks/`
   propagation is a documented follow-up.
2. **`block_on_failure` propagation** — `.cursor/hooks/g-hk-pre-commit.ps1` honors
   `$env:GALD3R_HOOK_BYPASS=1` only after the T600 patch is propagated from `.claude/hooks/`.
3. **MCP server set ❓** — config mechanism verified ✅; concrete server list is machine-specific
   (no `.cursor/mcp.json` committed), untested in CI.
4. **SCAN_DOCS not yet run** — `last_doc_scan: never`; doc-derived claims should be confirmed by a
   future `@g-platform-scan-docs cursor` crawl of https://docs.cursor.com.

> **Note (verified correction):** `hooks.json` is at `.cursor/hooks.json` (the `.cursor/` root),
> NOT inside `.cursor/hooks/`. The §2 folder-layout comment was clarified accordingly.

---

## 11. Hook Authoring — Idempotency Guard Pattern (T839)

Any hook that should only fire once per session (session-start, vault-reindex, vault-migrate, wrkspc-manifest-check) MUST include an idempotency guard at the top:

```powershell
# ── Idempotency guard ─────────────────────────────────────────────────────────
if (-not $ForceRun -and $env:GALD3R_HK_{HOOKNAME}_APPLIED -eq "1") {
    Write-Host "[SKIP] g-hk-{hookname} already applied this session. Pass -ForceRun to override."
    exit 0
}
$env:GALD3R_HK_{HOOKNAME}_APPLIED = "1"
```

**Naming**: replace `{HOOKNAME}` with the script name uppercased with underscores:
- `g-hk-session-start.ps1` → `GALD3R_HK_SESSION_START_APPLIED`
- `g-hk-vault-reindex.ps1` → `GALD3R_HK_VAULT_REINDEX_APPLIED`
- `g-hk-vault-migrate.ps1` → `GALD3R_HK_VAULT_MIGRATE_APPLIED`
- `g-hk-wrkspc-manifest-check.ps1` → `GALD3R_HK_WRKSPC_MANIFEST_CHECK_APPLIED`

**Exclusions** — hooks that MUST run every time are excluded from this guard:
- `g-hk-pcac-inbox-check.ps1` — explicitly re-callable for conflict resolution
- `g-hk-pre-commit.ps1` — must validate every commit
- `g-hk-validate-shell.ps1` — must validate every shell command
- `g-hk-pre-push.ps1` — must validate every push

**Always add `-ForceRun` param** so callers can bypass the guard when they explicitly need a re-run.

---

## 11a. Hook Companion `hook.md` Pattern (T1171)

Every gald3r hook script (`.cursor/hooks/g-hk-*.ps1`) MUST have a companion `hook.md` self-description file at the same path. Pattern harvested from OpenClaw Hooks Crash Course (V18 — Bdr7afGhh4I, 2026-05-13).

### Why

A `hook.md` companion is both **human documentation** AND a **runtime context payload**. When a hook fires under `preToolUse` (or another event), the harness SHOULD inject the matching `hook.md` content as `additional_context` so the agent knows what the hook just did and why a tool call was blocked / allowed / rewritten. Without this, agents see a deny verdict with no explanation and waste turns re-trying the same call.

### Canonical 5-section template

```markdown
# Hook: <hook-name>

## Fires On
<event description: trigger, matcher, idempotency story>

## What It Does
<2-3 sentence description of the hook's job>

## Side Effects
<files written, processes run, state changed, allow / deny verdicts>

## Related Tasks
<T### IDs that introduced or modify this hook>
```

Target length: ~30-60 lines per `hook.md`. Lean by design — full design docs live in `docs/<timestamp>_*_HOOK_*.md`. The companion is for runtime context, not encyclopedic reference.

### Authoring

- **Scaffolding**: use `@g-hook-create <hook-name> <event>` to create the `.ps1` + `hook.md` pair atomically.
- **Source of truth**: hook description lives in `hook.md`. `hooks.json` is for wiring only — do not duplicate the description.
- **Mirror policy**: same parity rules as the `.ps1`. The canonical copy lives in `.cursor/hooks/`; mirror to `.claude/hooks/`, `.agent/hooks/`, `.codex/hooks/`, `.opencode/hooks/` for every IDE that ships the corresponding `.ps1`. md5-verify after each propagation.

### Wiring in `hooks.json`

Each hook entry SHOULD reference its companion via a `"_hook_md"` field (informational, ignored by current Cursor parsers but documents the contract for the harness):

```json
{
  "command": "...powershell.exe ... -File .cursor/hooks/g-hk-session-start.ps1",
  "_hook_md": ".cursor/hooks/g-hk-session-start.md"
}
```

Top-level `_doc` in `hooks.json` documents the contract for new contributors.

### Session Lifecycle Hooks (T1057)

gald3r ships three hooks on the `stop` event for full session-end coverage:

1. `g-hk-agent-complete.ps1` — persists chat log, writes a reflection hint for the next session
2. `g-hk-nightly-learn.ps1` — every N sessions, dispatches LLM extraction into `.gald3r/learned-facts.md` (detached spawn pattern; configurable in `AGENT_CONFIG.md`)
3. `g-hk-session-end.ps1` (T1057) — appends a structured record to `.gald3r/logs/session_end.log` and overwrites `.gald3r/logs/session_end_pending.json` with a memory-capture pending marker for a future `memory_capture_session` MCP consumer

All three return `continue: true` immediately and never delay session close. PowerShell hooks cannot invoke MCP tools directly (the MCP client is the chat agent, not the shell), so `g-hk-session-end` stages the data and T1263 will wire the actual consumer.

### Available `preToolUse` Hooks

gald3r ships four hooks on the `preToolUse` event:

1. `g-hk-pre-tool-call-gald3r-guard.ps1` (matcher `Edit|Write|MultiEdit|NotebookEdit|...`) — `.gald3r/` agent-required gate
2. `g-hk-pre-tool-call-prd-freeze.ps1` — refuses Edit/Write to a released/superseded PRD (C-019)
3. `g-hk-pre-tool-call-member-gald3r-guard.ps1` — `controlled_member` `.gald3r/` marker-only guard
4. `g-hk-pre-tool-call.ps1` (matcher `Bash|Shell|Terminal|run_terminal_cmd`, T1106) — compresses large shell/terminal output to the last N lines + summary prefix, preserving the full block to `.gald3r/logs/tool_output_<session_id>.log`. N = `pre_tool_call_compress_lines` in `AGENT_CONFIG.md` (default 50; 0 = disabled). Non-blocking; error/warning lines from the truncated region are surfaced in the summary. Reports 60-90% token reduction in shell-heavy sessions.

---

## 10. Install Verification Checklist

```
✅ .cursor/rules/ has 8+ g-rl-*.mdc always-apply files
✅ .cursor/skills/ has gald3r core skills (g-skl-tasks, g-skl-bugs, g-skl-plan, etc.)
✅ .cursor/agents/ has gald3r agent files
✅ .cursor/commands/ has g-* command files
✅ .cursor/hooks/ has session-start and other PS1 hooks
✅ platform_parity_sync.ps1 reports 0 gaps
✅ Cursor > Settings > MCP shows configured servers (if using MCP)
```

---

## 11. Skill-as-Installer Pattern

Skills that wrap paid or OAuth-gated MCP services MUST include a `## Installation` section the agent executes automatically on first use — replacing the README that nobody reads.

### Three-state algorithm

```
1. ALREADY CONFIGURED — check .cursor/mcp.json for the server key → if present, skip
2. TOKEN / KEY FOUND  — check env vars / .env for SERVICE_API_KEY → write MCP entry, proceed
3. NOT SET UP        — open browser for OAuth or key retrieval, write entry on return
```

**Browser open (Windows / macOS):**
```powershell
# Windows (Shell tool)
Start-Process "https://service.com/api-keys"
# macOS / Linux
# open "https://service.com/api-keys"
```

### Cost Confirmation gate (credit-billed services)

Before any generation / consumption call, the agent MUST:
1. Quote: model + settings, estimated cost, current balance, projected balance after
2. Wait for explicit "go" / "yes" / "do it"
3. Never auto-proceed — even in background/auto mode

### `## Installation` template for new skills

```markdown
## Installation

Requires [ServiceName] [account / subscription tier].

**Agent-guided setup (runs automatically on first use):**

1. **Configured?** — check `.cursor/mcp.json` for `"service-name"` → skip if present
2. **Key found?** — check env `SERVICE_API_KEY` → write MCP entry, continue
3. **Not set up?** — `Start-Process "https://service.com/api-keys"` → paste key → write entry

> **Cost gate (if credit-billed):** quote cost + balance before every billable call; wait for "go".
```

See `higgsfield` skill for the reference implementation.

---

## 12. Skill Cost-Guard Pattern (T844)

Skills that call paid external APIs MUST surface a cost estimate and ask for explicit user confirmation before executing any billable operation.

### Template

```markdown
> "About to [describe operation] using [Service/Model] — estimated cost: [~N credits / $X].
> Continue? (**y** = proceed · **n** = cancel · **options** = see cheaper alternatives)"
```

Wait for explicit confirmation. If the user hesitates → offer cheaper alternatives (lower resolution, faster model, shorter duration, smaller batch).

### Rules

- Show the estimate BEFORE the API call — never after
- If the API supports balance queries, include projected remaining balance
- On cancel: confirm "Cancelled — no credits used"
- The negotiate-down flow MUST offer at least one cheaper alternative

See `skill-create` SKILL.md `## Cost-Guard Pattern` for the full authoring template.

---

## Zero-Cost Provider Options

### Nvidia NIM Free Tier

[Nvidia NIM](https://build.nvidia.com) offers a **1000 free API credits/month** with no credit card required — the best free option for gald3r users who want real cloud inference beyond Ollama.

| Detail | Value |
|--------|-------|
| Signup | https://build.nvidia.com |
| Free credits | 1000/month (no CC required) |
| Best for | reviewer, qa_engineer, task_manager roles |
| Not recommended for | primary orchestrator on heavy workloads |
| OpenRouter access | Use `provider: openrouter, model: nvidia/...` |

**Compatible models for gald3r roles**:
- `nimitron` — good for code review, structured output
- `glm4` — strong reasoning, suited for task management and QA

**Provider fallback config** (reference for AGENT_CONFIG.md `provider_fallback_chain`):
```yaml
reviewer:
  - provider: nvidia-nim
    model: nimitron
    tier: free
  - provider: ollama
    model: qwen2.5
    tier: offline
```

> Credit note: 1000 credits/month is sufficient for ~200-400 reviewer calls. Budget-conscious teams should reserve NIM for the reviewer/QA roles and use Ollama for task_manager.

---

## Local Model Inference Setup

For agents running on local hardware. Covers the two best local inference stacks.

### Mac (Apple Silicon) — OMLX by June Kim

[OMLX](https://github.com/junkim100/omlx) (13,000+ stars, Apache 2.0) provides tiered KV cache:
- **Hot cache**: RAM (instant)
- **Cold cache**: SSD disk (1-2s restore vs 30-90s cold)

Context restore 15-45× faster than standard llama.cpp. OpenAI/Anthropic API compatible.

```bash
# Install via Homebrew
brew install omlx

# Start server (OpenAI-compatible on localhost:11434)
omlx serve --model Qwen3-27B-Q4KM

# Configure in AGENT_CONFIG.md
provider_fallback_chain:
  code_generation:
    - provider: omlx
      model: Qwen3-27B-Q4KM
      tier: offline
```

### Windows/Linux — ik_llama.cpp (MTP fork)

[ik_llama.cpp](https://github.com/ikawrakow/ik_llama.cpp) is a performance-focused llama.cpp fork with **Multi-Token Prediction (MTP)** support. 3 CLI flags unlock ~20% speed boost.

```bash
# Build (same as llama.cpp)
git clone https://github.com/ikawrakow/ik_llama.cpp && cd ik_llama.cpp
cmake -B build -DGGML_CUDA=ON && cmake --build build -j$(nproc)

# Serve with MTP flags (20% speed boost on Qwen3)
./build/bin/llama-server \
  --model Qwen3-27B-Q4KM.gguf \
  --mtp \
  --draft-max 1 \
  --draft-p-min 0 \
  --port 11434
```

> **Note**: ik_llama.cpp is a fork; main features are pending upstream PR to mainline llama.cpp. Check [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases) first — MTP may have shipped in mainline since this was documented.

### Recommended Model

**Qwen3-27B Q4KM** — best balance for 16GB+ VRAM systems:
- Strong code generation and review quality
- 4-bit quantization fits in 16GB VRAM with overhead
- Fast enough for interactive use with MTP

### Ollama (Quick Start)

```bash
# Fastest setup path for both Mac and Windows/Linux
ollama pull qwen2.5:14b  # 14B model for 8GB VRAM
ollama pull qwen2.5:32b  # 32B model for 20GB+ VRAM
# Serves OpenAI-compatible API on localhost:11434 by default
```

### gald3r-lite context mode (small/local models — T1081)

When targeting a small/local model (≤8B, 4–32K window) the full ~300-line always-apply budget +
`AGENTS.md` + `CLAUDE.md` saturates the window. **gald3r-lite** is a defined, *safe* trim
(≤~2K-token system prompt). Classification:

- **Never-drop (safety):** `g-rl-34` (TODO/stub gate), `g-rl-35` (bug-discovery gate), the
  `.gald3r/` agent-gate + code-needs-task/bug + no-autonomous-push rules from `g-rl-33` (terse form).
- **Must-keep, compressed:** `g-rl-00` (footer/refactor/shell-probe), `g-rl-08` (PowerShell correctness).
- **Drop for lite:** `g-rl-25` (session-start), bulk of `g-rl-33` (swarm/PCAC/clean-gates),
  `g-rl-36` (workspace guard), `g-rl-26`, full `AGENTS.md` body — replace each with a 1-line pointer.
- **Stub:** `CLAUDE.md` → 5 lines (name, type, mission, "tasks in `.gald3r/`", "full rules on frontier sessions").
- **Roles:** reviewer / QA / verifier / single scoped implement are **lite-safe**; orchestrator /
  task-manager / planner (anything mutating shared `.gald3r/` state or coordinating agents) need **full context**.

Full design spec (rationale, budget composition, portable-mode tie-in): see
`docs/20260521_111712_Claude_GALD3R_LITE_CONTEXT_MODE_DESIGN.md`. The proxy that *applies* the
trim (OpenClaude `local-proxy.js`-style) is implementation, tracked under portable mode (T1082/T1084).
