<p align="center">
  <img src="logo/Gald3r_Logo_Big.jpg" alt="Gald3r" width="400" />
</p>

<h1 align="center">gald3r — give your AI coding tools one shared brain</h1>

<p align="center">
  Your AI assistants each start from zero, every session, in every tool.<br />
  gald3r drops a persistent, file-based brain into your repo — tasks, bugs, plans,
  and constraints that <strong>every</strong> AI tool reads and writes.<br />
  Plan in one tool. Code in another. Nothing is lost between them.
</p>

<p align="center">
  <a href="https://github.com/Gald3r-Labs/gald3r_core/releases"><img src="https://img.shields.io/badge/version-4.0.0-blue" alt="version 4.0.0" /></a>
  <a href="https://github.com/Gald3r-Labs/gald3r_core"><img src="https://img.shields.io/badge/engine-gald3r__core-6f42c1" alt="engine" /></a>
  <a href="https://github.com/Gald3r-Labs/gald3r_core/releases"><img src="https://img.shields.io/badge/OS-Windows%20%C2%B7%20macOS%20%C2%B7%20Linux-informational" alt="Windows, macOS, Linux" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-FSL--1.1--Apache-green" alt="license" /></a>
</p>

<p align="center">
  <a href="https://docs.gald3r.ai">Docs</a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="PLATFORM_SUPPORT.md">All 38 platforms</a>
</p>

---

## v4.0.0 — public beta

**The first three-platform signed release is out now (4.0.0-beta.3).**

| OS | Installers | Binaries |
|---|---|---|
| **Windows** | [**gald3r-windows-x86_64.msi**](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-windows-x86_64.msi) (signed) | [gald3r.exe](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-windows-x86_64.exe) · [gald3rw.exe](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3rw-windows-x86_64.exe) |
| **macOS** | [**gald3r-macos-arm64.pkg**](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-macos-arm64.pkg) (signed) | [gald3r](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-macos-arm64) |
| **Linux** | [**gald3r-linux-x86_64.tar.gz**](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-linux-x86_64.tar.gz) (with `install.sh`) | [gald3r](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-linux-x86_64) |

<sub>Authenticode-signed on Windows, Developer-ID codesigned + Apple-notarized on macOS,
sha256 sidecars on every asset. These links always resolve to the newest release.</sub>

Everything — the framework, all 38 platform overlays, the task engine — ships in
**one binary** and provisions from it. This repo is the product's front door; the
binary does the rest.

---

## The problem

You use Cursor for one thing and Claude Code for another. Maybe Copilot at work, Codex
on a side project, a local model when you're offline. Each one opens with no idea what
you decided yesterday, what's already broken, or what you told the last one never to touch.

So you re-explain. Every time. In every tool.

## What gald3r does

gald3r puts a `.gald3r/` folder in your project — plain markdown files for tasks, bugs,
plans, constraints, and cross-project coordination. Every AI coding tool you use reads
and writes the same files:

- **Tasks and bugs** that live in your repo, in your git history — not in one tool's memory
- **Constraints** your AI agents must follow — user-authored, per-project law
- **Plans and PRDs** that survive restarts, tool swaps, and team changes
- **A deterministic engine** (`gald3r`) that runs the boring parts with zero LLM calls

No accounts. No server. No database to operate. No Docker.

---

## Quick start

**1. Get the binary** — from **[gald3r_core releases](https://github.com/Gald3r-Labs/gald3r_core/releases)**:

| OS | Fastest path |
|---|---|
| **Windows** | Download `gald3r-windows-x86_64.msi`, run it, open a new terminal |
| **macOS** | Download `gald3r-macos-arm64.pkg`, double-click, follow the prompts |
| **Linux** | `curl -LO .../releases/latest/download/gald3r-linux-x86_64.tar.gz && tar xzf gald3r-linux-x86_64.tar.gz && ./gald3r-*-linux-x86_64/install.sh` |

Verify with `gald3r --version`. (Full per-OS instructions, checksums, and source builds:
**[docs.gald3r.ai/install](https://docs.gald3r.ai)**.)

**2. Put the brain in your project:**

```bash
cd /path/to/your/project
gald3r setup                      # creates .gald3r/ and walks you through
gald3r platform install cursor    # or: claude, codex, opencode, copilot, windsurf, ...
```

**3. Open your AI tool and go.** `/g-setup` in Claude Code, `@g-setup` in Cursor —
the brain is live and every AI you point at the repo can see it.

---

## The gald3r system — who does what

One product family, five pieces. ● owns it · ◐ involved in it.

| What you see | In plain terms | gald3r_core (engine) | gald3r_throne (desktop) | world_tree (cloud) | Framework (CRASH) | Longship (agent) | Docs |
|---|---|---|---|---|---|---|---|
| **Task, bug & plan tracking** | A file-based brain in your repo every AI reads and writes | ● owns the verbs + database | ◐ displays it | ◐ syncs it | ◐ defines the format | | [docs](https://docs.gald3r.ai) |
| **Rules & constraint enforcement** | Always-on behavioral guardrails + your own per-project law | ● owns the checker + `constraint` verbs | | | ● ships the rule packs | | [docs](https://docs.gald3r.ai) |
| **38 IDE/platform integrations** | Cursor, Claude Code, Codex, Copilot & 34 more, from one binary | ● generates every overlay | | | ● the content itself | | [matrix](PLATFORM_SUPPORT.md) |
| **Autonomous pipelines** | `g-go` / `g-go-go` — claim, implement, verify, review, unattended | ● owns the orchestration | | | ◐ defines the playbooks | ◐ execution plane | [docs](https://docs.gald3r.ai) |
| **Desktop workbench** | A native GUI over the same brain and engine | | ● owns it | | | | [throne](https://github.com/Gald3r-Labs/gald3r_throne) |
| **Cross-project coordination** | Projects ask/order/sync with each other (WPAC) | ◐ the client | | ◐ the registry | ● the protocol | | [docs](https://docs.gald3r.ai) |
| **Cloud sync & identity** | Multi-device sync and sign-in for teams | ◐ `gald3r valk` client | | ● owns it | | | [docs](https://docs.gald3r.ai) |
| **Memory & knowledge vault** | Cross-session agent memory + an Obsidian-compatible vault | ● owns it | | | | | [docs](https://docs.gald3r.ai) |
| **QA, review & security gates** | Deterministic validation that blocks bad state before it lands | ● owns the gates | | | ◐ the hooks that call them | | [docs](https://docs.gald3r.ai) |
| **Release & code signing** | One tag → signed binaries for all three OSes | ● owns the pipeline | | | | | [docs](https://docs.gald3r.ai) |
| **MCP server** | Other AI tools query your gald3r brain as MCP tools | ● owns it | | | | | [docs](https://docs.gald3r.ai) |

`gald3r_core`, `gald3r_throne`, `world_tree`, and `gald3r_longship` ship as compiled
binaries (the first two public, the rest private) — this repo carries the framework
they all serve, plus everything below.

---

## What's in this repo

This repo is gald3r's **front door** — a landing page, not an install dependency:

| Path | What it is |
|---|---|
| `README.md` | This page |
| `PLATFORM_SUPPORT.md` | The full 38-platform support matrix — with the honest gaps marked |
| `CHANGELOG.md` | Release history |
| `LICENSE`, `NOTICE` | License (FSL-1.1-Apache-2.0) |
| `VERSION` | Current version marker |

Everything that used to live here as file trees — the per-platform skill/command/rule
overlays and the project template — now **ships inside the binary** and is generated
by it: `gald3r platform install <platform>` writes the exact overlay for your AI tool,
always current with your binary version, on **all 38 supported platforms**. One binary,
every tool, no template copies to drift.

- **The engine**: [gald3r_core](https://github.com/Gald3r-Labs/gald3r_core) (releases)
- **The docs**: [docs.gald3r.ai](https://docs.gald3r.ai)
- **The desktop app**: [gald3r_throne](https://github.com/Gald3r-Labs/gald3r_throne)
- **Contributing**: development happens in the private engine repo — see
  [gald3r_core](https://github.com/Gald3r-Labs/gald3r_core) for the public mirror.

---

## License

[FSL-1.1-Apache-2.0](LICENSE) — free to use; converts to Apache 2.0 on the same
schedule. See [NOTICE](NOTICE) for attribution.
