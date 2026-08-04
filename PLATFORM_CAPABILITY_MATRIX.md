# PLATFORM_CAPABILITY_MATRIX.md — Feature Comparison Across Platforms

> **2026-08-03 reconciliation note:** this file previously cited a `strategy/gen_platform_docs.py`
> generator and a `strategy/PLATFORM_DATA.json` source that do not exist anywhere in this repo
> (nor a `COMBINED_READINESS.md` companion this file pointed to), and stated **34 platforms**
> against the actual **38** shipped in `platforms/`. Those references have been removed and the
> count corrected; the canonical roster now lives in
> [`platforms/PLATFORM_REGISTRY.yaml`](platforms/PLATFORM_REGISTRY.yaml). The `mimo-code`
> platform was missing a row entirely (added below, unverified) and `kilo_code`/`kiro_cli` used
> an underscore that doesn't match their actual `platforms/kilo-code` / `platforms/kiro-cli`
> directory names (corrected). **The per-platform ✅/⚠️/❌ capability cells themselves were left
> as-is** — re-verifying all 38 rows against each platform's current native surface is a larger
> audit than this pass covers; treat the existing cells as last-verified at whatever date
> preceded this note, not as freshly re-checked.

**38 platforms**, one shipped `platforms/<name>/` overlay per row (see
[`platforms/PLATFORM_REGISTRY.yaml`](platforms/PLATFORM_REGISTRY.yaml) for the canonical roster,
display names, and lifecycle/support-tier metadata).

Legend: ✅ verified · ⚠️ partial · ❌ not supported · ❓ untested.

| Platform | Hooks | Rules | Skills | Commands | MCP | Engine tier | Rules ext |
|---|---|---|---|---|---|---|---|
| aider | ⚠ | ✅ | ❌ | ⚠ | ❌ | CLI (L1) | .md |
| amp | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| antigravity | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| astrbot | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | — |
| augment | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| claude | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| cline | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| codebuddy | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | rules.md |
| codex | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| continue | ✅ | ✅ | ⚠ | ✅ | ✅ | MCP (L2) | .md |
| copilot | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| cursor | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .mdc |
| deepcode | ❌ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) | rules.md |
| gemini | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| goose | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| hermes | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | — |
| junie | ⚠ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| kilo-code | ❌ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | — |
| kimi | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | — |
| kiro | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| kiro-cli | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | — |
| mimo-code | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |
| mistral | ⚠ | ⚠ | ✅ | ⚠ | ✅ | MCP (L2) | rules.md |
| openclaw | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| opencode | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| openhands | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| qoder | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| qwen | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| replit | ❌ | ✅ | ✅ | ❌ | ✅ | MCP (L2) | .md |
| roo | ❌ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| trae | ❌ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) | .md |
| void | ❌ | ✅ | ❌ | ❌ | ✅ | MCP (L2) | .cursorrules |
| warp | ❌ | ✅ | ✅ | ⚠ | ✅ | MCP (L2) | .md |
| windsurf | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| zcode | ❌ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .md |
| zed | ❌ | ✅ | ✅ | ❌ | ✅ | MCP (L2) | .md |
| pi | ✅ | ✅ | ✅ | ✅ | ❌ | files-only (L0) | .md |
| subq | ❌ | ❌ | ❌ | ❌ | ❌ | files-only (L0) | .md |

---

**Capability columns** (unchanged from the canonical matrix) + the engine dimension:

| Column | Meaning |
|---|---|
| Hooks | Native lifecycle hook system + gald3r hook wiring |
| Rules | Persistent always-apply rules / memory injection |
| Skills | `g-skl-*/SKILL.md` discovery + invocation |
| Commands | `@g-*` slash commands / workflow equivalents |
| MCP | Model Context Protocol server support |
| **Engine tier** | how the bundled gald3r engine reaches the platform — **L2 MCP**, **L1 CLI** (`uv run … gald3r`), **L0 files-only** (no MCP/CLI reachability; T617 stub floor means the shipped `.md` files alone no longer carry actionable procedure text for this tier — see docs.gald3r.ai) |
| Rules ext | per-platform rule file extension (`.md` / `.mdc` / single-file), from `_platform_capabilities.json` |

The engine tier is the new column: even where a native capability is ❌/⚠️, the engine supplies that
behavior via MCP/CLI on most platforms — so the *effective* readiness is higher than the native
columns alone. (The "32/34"-style fraction and the dangling `COMBINED_READINESS.md` reference
this section previously carried have been removed — see the reconciliation note at the top of
this file.)
