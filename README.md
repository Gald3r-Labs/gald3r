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
  <a href="ROADMAP.md">Roadmap</a> ·
  <a href="PLATFORM_SUPPORT.html">All 38 platforms</a>
</p>

---

## v4.0.0 — public beta

**The first three-platform signed release is out now (4.0.0-beta.3).**

| OS | Download |
|---|---|
| **Windows** | [**gald3r-windows-x86_64.msi**](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-windows-x86_64.msi) (signed installer) · [gald3r.exe](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-windows-x86_64.exe) · [gald3rw.exe](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3rw-windows-x86_64.exe) |
| **macOS** | [**gald3r-macos-arm64.pkg**](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-macos-arm64.pkg) (signed installer) · [gald3r](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-macos-arm64) (bare binary) |
| **Linux** | [**gald3r-linux-x86_64.tar.gz**](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-linux-x86_64.tar.gz) (with `install.sh`) · [gald3r](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-linux-x86_64) (bare binary) |

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

## What's in this repo

This repo is gald3r's **front door** — a landing page, not an install dependency:

| Path | What it is |
|---|---|
| `README.md` | This page |
| `PLATFORM_SUPPORT.html` | The full 38-platform support matrix |
| `ROADMAP.md` | Where the product is going |
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
