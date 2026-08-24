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
  <a href="https://github.com/Gald3r-Labs/gald3r_core/releases"><img src="https://img.shields.io/github/v/release/Gald3r-Labs/gald3r_core?include_prereleases&label=version&color=blue" alt="latest gald3r version" /></a>
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

<h2 align="center">🎬 COMING SOON — your AI team gets a face. And a stage. And a show.</h2>

<p align="center">
  <img src="https://img.shields.io/badge/status-in%20the%20studio-ff2d78?style=for-the-badge" alt="in the studio" />
  <img src="https://img.shields.io/badge/going-LIVE%20soon-8a2be2?style=for-the-badge" alt="going live soon" />
  <img src="https://img.shields.io/badge/24%2F7-broadcast-ffb400?style=for-the-badge" alt="24/7 broadcast" />
</p>

<p align="center"><strong>Stop watching scrolling logs.</strong><br/>
gald3r's next act puts your entire AI crew inside a living, walkable 3D world —<br/>
characters with names, faces, voices, and desks, performing your project's <em>real work</em> in real time.<br/>
Watch them huddle over a bug. Argue in the war room. Celebrate a release by the pool.<br/>
Then step in yourself — on screen or in VR — and run the room.</p>

<!-- STUDIO SHOTS: drop captures into assets/studio/ and uncomment
<p align="center">
  <img src="assets/studio/shot_01.jpg" width="49%" alt="the estate, live" />
  <img src="assets/studio/shot_02.jpg" width="49%" alt="the war room at work" />
</p>
<p align="center">
  <img src="assets/studio/shot_03.jpg" width="49%" alt="poolside, off hours" />
  <img src="assets/studio/shot_04.jpg" width="49%" alt="night shift" />
</p>
-->

<p align="center">And it's bigger than code. The same stage is built for <strong>every kind of project gald3r runs</strong> —<br/>
podcasts and newscasts with an anchor desk, music and video productions, episodic shows, skits,<br/>
choose-your-own-adventure worlds — describe your set in plain words, drop in reference pictures,<br/>
and the creator studio builds the world, the cast, and the show around <em>your</em> project.<br/>
Any project type. Any theme. Yours. Broadcast it 24/7.</p>

<p align="center"><em>Built on the gald3r engine below — the shared brain becomes a shared world.<br/>
First look is coming to the stream. Watch this space.</em></p>

---

## v5.0.0 — public beta

**The Go rewrite is out now — signed on Windows, macOS, and Linux.** The version badge above always shows the newest release; every link below resolves to it.

| OS | Installer | Portable (all binaries) |
|---|---|---|
| **Windows** | [**gald3r-windows-x86_64.msi**](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-windows-x86_64.msi) (signed) | [gald3r-windows-x86_64.zip](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-windows-x86_64.zip) |
| **macOS** | [**gald3r-macos-arm64.pkg**](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-macos-arm64.pkg) (signed) | [gald3r-macos-arm64.tar.gz](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-macos-arm64.tar.gz) |
| **Linux** | [**gald3r-linux-x86_64.tar.gz**](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-linux-x86_64.tar.gz) (with `install.sh`) | [gald3r-linux-x86_64.tar.gz](https://github.com/Gald3r-Labs/gald3r_core/releases/latest/download/gald3r-linux-x86_64.tar.gz) |

<sub>Authenticode-signed on Windows, Developer-ID codesigned + Apple-notarized on macOS,
sha256 sidecars on every asset. These links always resolve to the newest release.</sub>

**Companion apps** — optional, installed separately:

| App | What it is | Get it |
|---|---|---|
| **Throne** | Desktop control center for gald3r projects (Windows/macOS/Linux) | `gald3r install throne` — fetches the latest signed build from [gald3r_throne releases](https://github.com/Gald3r-Labs/gald3r_throne/releases) (minisign-verified) |
| **Longship** | Terminal UI for chat + swarm work, same engine | Built on the same engine — public distribution lands in an upcoming beta |

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

<!-- BEGIN: gald3r-platform-list -->
## Supported Platforms

gald3r installs the same `.gald3r/` task board, bug tracker, and CRASH overlay into every platform below — one binary, `gald3r platform install <name>`, and the files that platform actually reads land in your project. Full capability breakdown: [PLATFORM_SUPPORT.md](PLATFORM_SUPPORT.md).

- **[Aider](https://gald3r-labs.github.io/gald3r_core/latest/platforms/aider/)** — also searched as aider-chat, Aider AI
- **[Amp](https://gald3r-labs.github.io/gald3r_core/latest/platforms/amp/)** — also searched as Amp Code, Sourcegraph Amp
- **[AstrBot](https://gald3r-labs.github.io/gald3r_core/latest/platforms/astrbot/)**
- **[Augment Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/augment/)** — also searched as Auggie, Auggie CLI
- **[Claude Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/claude/)** — also searched as Claude, Anthropic Claude Code
- **[Cline](https://gald3r-labs.github.io/gald3r_core/latest/platforms/cline/)**
- **[Continue.dev](https://gald3r-labs.github.io/gald3r_core/latest/platforms/continue/)** — also searched as Continue
- **[Cursor](https://gald3r-labs.github.io/gald3r_core/latest/platforms/cursor/)** — also searched as Cursor IDE
- **[Deep Code CLI](https://gald3r-labs.github.io/gald3r_core/latest/platforms/deepcode/)** — also searched as Deep Code, deepcode-cli
- **[Devin Desktop](https://gald3r-labs.github.io/gald3r_core/latest/platforms/windsurf/)** — also searched as Windsurf, Cascade IDE
- **[GitHub Copilot](https://gald3r-labs.github.io/gald3r_core/latest/platforms/copilot/)** — also searched as Copilot, GitHub Copilot CLI
- **[Google Antigravity](https://gald3r-labs.github.io/gald3r_core/latest/platforms/antigravity/)** — also searched as Antigravity IDE, Antigravity
- **[Goose](https://gald3r-labs.github.io/gald3r_core/latest/platforms/goose/)** — also searched as Block Goose, Goose AI agent
- **[Hermes Agent](https://gald3r-labs.github.io/gald3r_core/latest/platforms/hermes/)** — also searched as Nous Hermes Agent, Nous Research Hermes
- **[JetBrains Junie](https://gald3r-labs.github.io/gald3r_core/latest/platforms/junie/)** — also searched as Junie
- **[Kilo Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/kilo-code/)** — also searched as KiloCode
- **[Kimi Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/kimi/)** — also searched as Kimi Code CLI, Moonshot Kimi Code, kimi-cli
- **[Kiro](https://gald3r-labs.github.io/gald3r_core/latest/platforms/kiro/)** — also searched as Kiro IDE, Amazon Kiro
- **[Kiro CLI](https://gald3r-labs.github.io/gald3r_core/latest/platforms/kiro-cli/)** — also searched as Amazon Q Developer CLI, Q Developer CLI
- **[Mistral Vibe CLI](https://gald3r-labs.github.io/gald3r_core/latest/platforms/mistral/)** — also searched as mistral-vibe, Mistral Code
- **[OpenAI Codex](https://gald3r-labs.github.io/gald3r_core/latest/platforms/codex/)** — also searched as Codex CLI, Codex
- **[OpenClaw](https://gald3r-labs.github.io/gald3r_core/latest/platforms/openclaw/)**
- **[OpenCode](https://gald3r-labs.github.io/gald3r_core/latest/platforms/opencode/)** — also searched as sst/opencode
- **[OpenHands](https://gald3r-labs.github.io/gald3r_core/latest/platforms/openhands/)** — also searched as All Hands AI, OpenDevin
- **[Pi](https://gald3r-labs.github.io/gald3r_core/latest/platforms/pi/)** — also searched as badlogic/pi-mono, Pi coding agent
- **[Qoder](https://gald3r-labs.github.io/gald3r_core/latest/platforms/qoder/)** — also searched as Alibaba Qoder
- **[Qwen Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/qwen/)** — also searched as Alibaba Qwen Code
- **[Replit Agent](https://gald3r-labs.github.io/gald3r_core/latest/platforms/replit/)** — also searched as Replit
- **[Roo Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/roo/)** — also searched as Roo Cline
- **[SubQ Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/subq/)** — also searched as SubQ
- **[Tencent CodeBuddy Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/codebuddy/)** — also searched as CodeBuddy
- **[TRAE](https://gald3r-labs.github.io/gald3r_core/latest/platforms/trae/)** — also searched as ByteDance TRAE, TRAE IDE
- **[Void](https://gald3r-labs.github.io/gald3r_core/latest/platforms/void/)** — also searched as Void IDE
- **[Warp](https://gald3r-labs.github.io/gald3r_core/latest/platforms/warp/)** — also searched as Warp terminal, Warp Oz
- **[Xiaomi MiMo-Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/mimo-code/)** — also searched as MiMo-Code, MiMo Code
- **[ZCode](https://gald3r-labs.github.io/gald3r_core/latest/platforms/zcode/)** — also searched as Z.ai ZCode, GLM ZCode
- **[Zed](https://gald3r-labs.github.io/gald3r_core/latest/platforms/zed/)** — also searched as Zed Editor

<!-- END: gald3r-platform-list -->

---

## Works With

gald3r doesn't just live *inside* Claude Code and Cursor — it can drive them headlessly for
autonomous pipelines, and it talks straight to your model backend of choice, local or cloud:

| Backend | What it is | Docs |
|---|---|---|
| **[Claude Code](https://gald3r-labs.github.io/gald3r_core/latest/platforms/claude/)** | Anthropic's terminal coding agent — `g-go`/`g-go-go` drive it headlessly for autonomous coding | [Platform guide](https://gald3r-labs.github.io/gald3r_core/latest/platforms/claude/) |
| **[Cursor](https://gald3r-labs.github.io/gald3r_core/latest/platforms/cursor/)** | The `cursor-agent` CLI — same headless autopilot story, one flag away | [Platform guide](https://gald3r-labs.github.io/gald3r_core/latest/platforms/cursor/) |
| **[Ollama](https://ollama.com)** | Local model runtime — `gald3r init-providers` auto-discovers every model you've pulled | [Provider docs](https://gald3r-labs.github.io/gald3r_core/latest/providers/) |
| **[LM Studio](https://lmstudio.ai)** | Local model runtime with a GGUF library and its own local server | [Provider docs](https://gald3r-labs.github.io/gald3r_core/latest/providers/) |
| **[OpenRouter](https://openrouter.ai)** | One API key, every hosted model — `openai_compat`, no adapter needed | [Provider docs](https://gald3r-labs.github.io/gald3r_core/latest/providers/) |
| **Unsloth Studio** ![NEW](https://img.shields.io/badge/NEW-orange?style=flat-square) | Built-in `unsloth` provider id, bearer-token auth, `localhost:8888/v1` by default — gald3r's first-supporter, day-one integration | [Provider docs](https://gald3r-labs.github.io/gald3r_core/latest/providers/) |

Full local + cloud provider setup: **[Models & Providers](https://gald3r-labs.github.io/gald3r_core/latest/providers/)**.

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
| **Live coordination backbone (Valkyrie)** | Agents message you and each other mid-run; the local brain syncs to the cloud | ◐ the `gald3r valk` connector | ◐ its inbox | ● the sync target | ◐ the ledger format | | [docs](https://docs.gald3r.ai) |
| **Cloud sync & identity** | Multi-device sync and sign-in for teams | ◐ `gald3r valk` client | | ● owns it | | | [docs](https://docs.gald3r.ai) |
| **Memory & knowledge vault** | Scoped cross-session memory (project/user/client), stash & reload for long runs, Obsidian-compatible vault | ● owns it | | ◐ sync (roadmap) | | | [docs](https://docs.gald3r.ai) |
| **Personality system** | A startup team of Norse gods voices your agents — Thor on performance, Sindri on craft, Loki on creative breakage | ◐ activation layer | ◐ shows it | | ● the persona packs | | [docs](https://docs.gald3r.ai) |
| **Skill packs** | Curated capability bundles per project type — install a pack, get its skills locked to it | ● owns `skill-pack` / `skills-lock` | | | ● the bundles | | [docs](https://docs.gald3r.ai) |
| **Third-party plugins** | Install plugins from any git repo; enable/disable per project | ● owns `gald3r plugin` | | | ◐ SKILL.md format | | [docs](https://docs.gald3r.ai) |
| **Themed reports** | Status, review, and backlog reports rendered in your chosen theme | ● the render engine | ◐ displays it | | ● theme definitions | | [docs](https://docs.gald3r.ai) |
| **Workspace-Control** | One control project governs many repos, with guarded member boundaries | ● owns it | | | ◐ the manifest format | | [docs](https://docs.gald3r.ai) |
| **Experiments framework** | Hypotheses with measurable gates and failure autopsies, tracked like code | ● owns it | | | ◐ the experiment format | | [docs](https://docs.gald3r.ai) |
| **Generated CRASH reference** | The full user-facing catalog of every command, skill, rule, agent, and hook shipped | ● generates it from source | | | ● the corpus | | [docs](https://docs.gald3r.ai) |
| **Multi-format output** | The same reports as markdown, HTML, JSON, or TOON — for humans and agents | ● owns it | | | | | [docs](https://docs.gald3r.ai) |
| **QA, review & security gates** | Deterministic validation that blocks bad state before it lands | ● owns the gates | | | ◐ the hooks that call them | | [docs](https://docs.gald3r.ai) |
| **Release & code signing** | One tag → signed binaries for all three OSes | ● owns the pipeline | | | | | [docs](https://docs.gald3r.ai) |
| **MCP server** | Other AI tools query your gald3r brain as MCP tools | ● owns it | | | | | [docs](https://docs.gald3r.ai) |

`gald3r_core`, `gald3r_throne`, `world_tree`, and `gald3r_longship` ship as compiled
binaries (the first two public, the rest private) — this repo carries the framework
they all serve, plus everything below.

### In the forge — honestly unfinished

Marketable, on the way, and labeled as such:

| In the forge | What it becomes | Where it lives today |
|---|---|---|
| **Marketplace** | A curated, signed plugin registry on world_tree | Design (blocked on the cloud registry); git-installed plugins work today |
| **Custom themes** | A visual editor for your own report themes | Theme definitions ship; editor in progress |
| **Suite installer** | One manifest install: core + longship + throne together | Design complete; implementation next |
| **Scoped memory sync** | Your memory follows you across machines | Local memory shipped; cloud sync on the roadmap |

---

## What's in this repo

This repo is gald3r's **front door** — a landing page, not an install dependency:

| Path | What it is |
|---|---|
| `README.md` | This page |
| `PLATFORM_SUPPORT.md` | The full 38-platform support matrix — with the honest gaps marked |
| `platforms/` | Per-platform reference docs — how each tool's project structure and extension surfaces actually work |
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
