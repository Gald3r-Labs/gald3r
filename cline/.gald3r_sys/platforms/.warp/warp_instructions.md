# Warp Platform — gald3r Configuration Guide

**Platform**: Warp (AI-native terminal — Active AI + Agent Mode + Cloud Agents + Warp Drive)
**Config Surface**: root `AGENTS.md` / `WARP.md` project rules + auto-discovered MCP config + Warp Drive Workflows (`.warp/workflows/`)
**gald3r Version**: 1.0.0
**Official Docs**: https://docs.warp.dev
**Authoritative skill**: `g-skl-platform-warp`
**Platform findings**: see `PLATFORM_SPEC.md` in this directory (the authoritative,
T1483-verified capability picture — read it before trusting any summary below)

---

## What Warp Is

Warp is an AI-native **terminal** (not an IDE). It has no file tree and no editor pane.
Its AI surface splits into **Active AI** (always-on inline hints), **Agent Mode**
(interactive multi-step task execution), and **Cloud Agents** (autonomous,
event-triggered runs on Warp's infrastructure). Its configurable primitives are
**project Rules files** (`AGENTS.md` / `WARP.md`), **MCP servers**, and **Warp Drive**
(a cloud-backed store of Workflows, Notebooks, Prompts, and Environment Variables).

---

## Folder Layout

```
<project-root>/
├── AGENTS.md               # Warp's default project rules file (/init generates it) — gald3r writes
├── WARP.md                 # all-caps rules file; takes priority over AGENTS.md if both exist — gald3r writes
├── .mcp.json               # MCP servers (auto-discovered by Warp; gitignored per g-rl-02) — shared
└── .warp/
    └── workflows/          # Warp Drive Workflow stubs (gald3r status / commit) — reference only
        ├── gald3r-status.yaml
        └── gald3r-commit.yaml

~/.warp/                    # Warp's own local app state (themes, launch configs) — platform-owned
~/.claude.json             # MCP servers (auto-discovered by Warp) — shared, machine-specific
.codex/config.toml         # MCP servers (auto-discovered by Warp) — shared
(Warp Drive)               # Workflows / Notebooks / Prompts / Env vars — CLOUD, not on disk
```

---

## Capability Map (from PLATFORM_SPEC.md)

| Capability | Status | How gald3r reaches Warp |
|---|---|---|
| **Rules** | ⚠️ partial | Real native auto-applying project rules via root `AGENTS.md` / `WARP.md`. BUT single-file markdown only — **no** `.mdc` files, **no** glob-scoped rule files. gald3r's `g-rl-*` set must be **flattened into** `AGENTS.md` / `WARP.md` prose. |
| **MCP** | ✅ first-class | Warp **auto-discovers** existing MCP server configs from `~/.claude.json`, root `.mcp.json`, and `.codex/config.toml`. The same server set is shared with Claude Code and Codex — no per-tool re-config. |
| **Commands** | ⚠️ partial | Warp's command primitive is the **Warp Drive Workflow** (parameterized, cloud-backed). gald3r ships workflow stubs below, but they are **not** auto-installed from on-disk `commands/g-*.md` — import them into Warp Drive manually. Custom slash commands are an open Warp RFC (#6857). |
| **Skills** | ❌ not supported | Warp has **no** on-disk `SKILL.md` discovery/auto-load. Warp Drive (cloud) is the closest analogue but is not repo-installable. A skill's instructions only reach Warp if copied into `AGENTS.md` / `WARP.md` or recreated manually as a Warp Drive Notebook. |
| **Agents** | ❌ not supported | Warp has **no** agent-definition-file discovery (no `g-agnt-*.md` roster). Active AI / Agent Mode / Cloud Agents are *operating modes of one assistant*, not loadable gald3r agents. Agent behaviors can only be described inside `AGENTS.md` / `WARP.md`. |
| **Hooks** | ❌ not supported | Warp has **no** lifecycle-event system — no `sessionStart`, `stop`, `preToolUse`, `beforeShellExecution`, no `hooks.json`. Agent hooks are an open Warp RFC (#6857). gald3r `.ps1` session-start / inbox / pre-commit hooks **do not auto-fire** on Warp; run them manually in the terminal. Cloud Agents are an agent-run trigger, **not** a local hook bus. |

> **Hard gaps (not achievable on Warp from the repo today):** on-disk skills, on-disk
> agents, extensible on-disk commands, and lifecycle hooks. The capabilities that map
> cleanly are **project Rules** (`AGENTS.md` / `WARP.md`, auto-applied) and **MCP**
> (auto-discovered shared config). This is the correct factual picture for a
> terminal-native platform — not an implementation failure.

---

## Primary Integration: Project Rules (`AGENTS.md` / `WARP.md`)

This is Warp's strongest gald3r fit and the **primary enforcement surface**.

- Warp auto-discovers `AGENTS.md` and `WARP.md` at the repo root. The filename must be
  **ALL-CAPS** to be recognized. If both exist in the same directory, **`WARP.md` wins**.
- `AGENTS.md` is the default `/init` generates (matching the cross-tool `AGENTS.md`
  convention), so `CLAUDE.md` / `GEMINI.md`-style instructions can be folded into the
  shared `AGENTS.md`.
- **Precedence** (most specific first): (1) rules file in the current subdirectory,
  (2) rules file in the repo root, (3) Global Rules (app-level, all projects).
- Project Rules apply **automatically** when an agent operates inside the project — no
  manual pin required.
- Place gald3r enforcement in the **root `AGENTS.md` / `WARP.md`** so it applies
  project-wide. Reference `.gald3r/learned-facts.md` from there if you want Warp to
  pick up durable project facts.

---

## MCP (first-class — no extra config)

Any MCP server gald3r relies on that is already declared in `.mcp.json`,
`~/.claude.json`, or `.codex/config.toml` is **reused by Warp automatically**. There is
no dedicated `.warp/mcp.json` to maintain. Manage servers through Warp's settings/UI or
the shared config files above.

> The concrete active server set is per-machine and untested in CI; the *mechanism* is
> verified from docs, not from a live install.

---

## Warp Drive Workflows (commands analogue)

gald3r ships workflow stubs that map to common operations. Import them into Warp Drive
(or keep them as project-local reference / run the underlying shell directly):

- **`.warp/workflows/gald3r-status.yaml`** — show active / pending / awaiting-review gald3r tasks.
- **`.warp/workflows/gald3r-commit.yaml`** — create a task-scoped commit.

These are **not** auto-installed as native `@g-*` / `/g-*` commands — Warp has no
`.warp/commands/` folder scan. Custom slash commands remain an open Warp RFC (#6857).

---

## Optional: Shell Profile Context (supplementary only)

Because Warp is terminal-native, you *may* also surface gald3r context into the shell
session as a convenience. This is **supplementary** — the project Rules files above are
the real instruction surface, not these env vars:

```bash
export GALD3R_ACTIVE_TASK=$(grep '\[🔄\]' .gald3r/TASKS.md 2>/dev/null | head -1)
export GALD3R_PROJECT=$(head -3 .gald3r/PROJECT.md 2>/dev/null)
```

---

## gitignore Decision (T1277 AC6)

`.warp/workflows/*.yaml` are **source** — keep them tracked. Warp's user config
(`~/.warp/`) is outside the project. `.mcp.json` is gitignored per `g-rl-02` (it is
machine-specific MCP config). No generated project output dir needs gitignoring.

---

## Verification

```powershell
Test-Path .warp/workflows          # workflow stubs present
Test-Path AGENTS.md                # project rules file present (or WARP.md)
```

---

## Common Pitfalls

- **Rules ARE supported** — earlier gald3r docs claimed Warp had "no project rules
  file". That is no longer true: Warp auto-applies `AGENTS.md` / `WARP.md`. Put gald3r
  enforcement there, not only in shell env vars.
- Warp's `g-rl-*` rules must be **flattened** into the single root rules file — there is
  no `.mdc` / glob scoping.
- Skills, agents, and lifecycle hooks have **no on-disk home** on Warp — do not expect
  the gald3r skill/agent/hook folders or `.ps1` hooks to auto-fire here.
- Warp Drive Workflows are cloud-backed — set up the Warp Drive workspace before team
  sharing; they are not installed automatically from the repo.
