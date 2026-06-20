---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: mimo
authoring_path: create
docs_url: https://mimo.xiaomi.com/mimocode
docs_url_secondary:
  - https://github.com/XiaomiMiMo/MiMo-Code
  - https://mimo.xiaomi.com/mimocode/agents
  - https://mimo.xiaomi.com/mimocode/start
crawl_max_age_days: 7
vault_doc_path: research/platforms/mimo/
last_doc_scan: 2026-06-13
reference: g-skl-platform-opencode
status: ⚠️
gald3r_support_tier: T2
task: T1484
---

# PLATFORM_SPEC.md — Xiaomi MiMo-Code

**Terminal-native AI coding agent with cross-session memory. Fork of OpenCode. Launched June 2026.**

MiMoCode is a terminal-native AI coding assistant built by Xiaomi as a fork of
[OpenCode](https://github.com/anomalyco/opencode). It inherits all core OpenCode capabilities
(TUI, LSP, MCP, multiple providers, plugins) and adds persistent cross-session memory,
intelligent context management, subagent orchestration, goal-driven autonomous loops,
Compose mode for specs-driven development, and self-improvement via Dream/Distill.

**Why this matters for gald3r early-mover advantage**: MiMo-Code launched June 10, 2026,
gained 7.6k GitHub stars and 610 forks within days, supports `AGENTS.md` + `CLAUDE.md`
natively, has an MCP layer, and ships with a Compose mode very similar to gald3r's `g-go`
pipeline. Early gald3r support = high-value SEO/GEO traffic and developer adoption signal.

---

## 1. Folder Hierarchy

gald3r writes to the repo-root `.mimocode/` folder. Verified layout from source/docs:

```
<project-root>/
├── AGENTS.md                          ← primary instruction file (read natively)
├── CLAUDE.md                          ← Claude Code compat file (also read)
├── MEMORY.md                          ← persistent project knowledge (auto-maintained)
├── checkpoint.md                      ← session state snapshot (auto)
├── notes.md                           ← scratch notes (auto)
└── .mimocode/
    ├── mimocode.json                  ← primary config (project-level)
    ├── agents/
    │   └── *.md                       ← custom agent definitions (YAML frontmatter + prompt)
    ├── prompts/
    │   └── *.txt                      ← prompt files referenced from mimocode.json
    └── tasks/
        └── <id>/progress.md           ← per-task progress logs (auto)

~/.config/mimocode/
├── mimocode.json                      ← global config
└── agents/                            ← global custom agent definitions
```

---

## 2. CRASH Primitive Support

| Primitive | Support | Notes |
|---|---|---|
| **Hooks** | ⚠️ Partial | Inherits from OpenCode. Session hooks exist; lifecycle events need verification |
| **Rules** | ✅ Native | `AGENTS.md` at project root read natively. Also reads `CLAUDE.md` |
| **Skills** | ⚠️ Via Compose | Compose mode workflows = Skills equiv. `/distill` auto-generates reusable skills |
| **Commands** | ✅ Native | `/goal`, `/dream`, `/distill`, `/voice`, custom slash commands via Compose |
| **MCP** | ✅ Native | `mcp` section in `mimocode.json`; inherits full OpenCode MCP layer |
| **Agents** | ✅ Native | `.mimocode/agents/*.md` (project) or `~/.config/mimocode/agents/` (global) |

---

## 3. Instruction Files (Rules)

MiMo-Code natively reads **both** `AGENTS.md` and `CLAUDE.md` at the project root:

```markdown
# AGENTS.md — gald3r rules injected here
<!-- Injected by gald3r install -->
<!-- Platform: mimo -->

## Project Context
...all gald3r AGENTS.md content...
```

Additionally, `MEMORY.md` serves as a persistent knowledge file that the agent maintains
automatically across sessions — this is MiMo-Code's equivalent of the gald3r vault.

**Load order** (verified from docs + source):
1. `~/.config/mimocode/mimocode.json` global config
2. `.mimocode/mimocode.json` project config (overrides global)
3. `AGENTS.md` → `CLAUDE.md` at project root
4. `MEMORY.md` injected into context window automatically

---

## 4. Skills (Compose Mode + Distill)

MiMo-Code's Compose mode provides structured specs-driven development with built-in
sub-workflows: planning, execution, code review, TDD, debugging, verification, and merging.

The `/distill` command auto-generates reusable skills from repeated workflows:

```
/distill
→ Scans recent session traces
→ Packages repeated workflows into .mimocode/agents/{name}.md skill files
→ Immediately available as sub-agents
```

**gald3r SKILL.md compatibility**: Place `SKILL.md` files in `.mimocode/agents/` with the
MiMo-Code frontmatter format. gald3r skills can be adapted with a thin wrapper:

```markdown
---
description: "Gald3r skill: g-skl-tasks"
mode: subagent
model: mimo/mimo-v2.5-pro
tools:
  write: true
  edit: true
  bash: false
---
<!-- SKILL.md content here -->
```

---

## 5. Commands (Slash Commands)

**Built-in commands**:

| Command | Description |
|---|---|
| `/goal <condition>` | Set a stopping condition; judge model validates completion |
| `/dream` | Extract recent knowledge into `MEMORY.md`, remove stale entries |
| `/distill` | Auto-package repeated workflows into reusable skills/agents |
| `/voice` | Enable voice input (MiMo logged-in users) |

**Custom commands** via Compose mode config in `mimocode.json`:

```json
{
  "compose": {
    "workflows": {
      "review": {
        "description": "Full code review workflow",
        "steps": ["plan", "review", "verify"]
      }
    }
  }
}
```

---

## 6. Hooks

MiMo-Code inherits OpenCode's hook architecture. OpenCode hooks fire on session events.
**Pending verification**: confirm `.mimocode/hooks.json` or equivalent hook registration.

Likely hook events (from OpenCode heritage):
- `session_start` — inject context from MEMORY.md + AGENTS.md
- `before_tool_call` — gate tool permissions
- `session_end` — trigger checkpoint save

**gald3r hook files**: Target `.mimocode/hooks.json` once doc crawl confirms the schema.

---

## 7. MCP Configuration

MCP is configured in `mimocode.json` under the `mcp` key (OpenCode-compatible syntax):

```json
{
  "$schema": "https://mimo.xiaomi.com//config.json",
  "mcp": {
    "gald3r": {
      "type": "remote",
      "url": "https://your-gald3r-instance/mcp",
      "enabled": true
    },
    "filesystem": {
      "type": "local",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

**gald3r MCP wire-up**: Add the gald3r MCP endpoint to `.mimocode/mimocode.json` during
`gald3r install --platform mimo`. This gives MiMo-Code agents access to all 42 gald3r tools.

---

## 8. Agents

Custom agents are defined as markdown files with YAML frontmatter:

```
.mimocode/agents/gald3r-reviewer.md
```

```markdown
---
description: "gald3r code review agent"
mode: subagent
model: mimo/mimo-v2.5-pro
temperature: 0.1
tools:
  write: false
  edit: false
  bash: false
---

You are a gald3r-aware code reviewer. Apply the g-go-review criteria:
security, quality, acceptance criteria, and hallucination guard.
Follow .gald3r/CONSTRAINTS.md rules. Report findings as BUG[BUG-NNN] entries.
```

**Built-in primary agents** (press `Tab` to switch):

| Agent | Mode | Description |
|---|---|---|
| `build` | primary | Full tool permissions for development |
| `plan` | primary | Read-only analysis and solution design |
| `compose` | primary | Specs-driven development orchestration |

---

## 9. Memory System (Unique to MiMo)

MiMo-Code's persistent memory is a key differentiator from other OpenCode forks:

| Memory File | Purpose | Auto-managed? |
|---|---|---|
| `MEMORY.md` | Persistent project knowledge, rules, architecture decisions | via `/dream` |
| `checkpoint.md` | Session state snapshot (task progress, recent context) | Auto on context limit |
| `notes.md` | Temporary scratch area for agents | Auto |
| `tasks/<id>/progress.md` | Per-task progress logs | Auto |

**gald3r + MiMo memory synergy**: `MEMORY.md` is MiMo's equivalent of gald3r's vault notes.
Consider wiring the gald3r `@g-memory-capture` workflow to write summaries to both
`.gald3r/vault/` AND `MEMORY.md` when running in a MiMo-Code project.

---

## 10. gald3r Installation

### Install Path

```
<project-root>/
├── AGENTS.md                ← gald3r injects rules here (natively read)
├── CLAUDE.md                ← gald3r injects Claude Code compat layer
└── .mimocode/
    ├── mimocode.json        ← gald3r adds MCP entry here
    └── agents/
        └── g-agnt-*.md      ← gald3r agents adapted to MiMo format
```

### Install Command (when implemented)

```bash
gald3r install --platform mimo
```

This should:
1. Write `AGENTS.md` (instruction file) at project root
2. Add gald3r MCP endpoint to `.mimocode/mimocode.json`
3. Place adapted gald3r agents in `.mimocode/agents/`
4. Write `MEMORY.md` with initial project memory seed
5. Confirm readback: `mimo read AGENTS.md` should load rules

### Verification Checklist

- [x] `AGENTS.md` read natively at session start ✅ (confirmed from docs)
- [x] `CLAUDE.md` read natively ✅ (visible in MiMo-Code repo root)
- [x] MCP servers configurable in `mimocode.json` ✅ (confirmed from docs)
- [x] Custom agents via `.mimocode/agents/*.md` ✅ (confirmed from docs)
- [ ] Hooks schema confirmed (verify `.mimocode/hooks.json` or equivalent)
- [ ] Skills/Compose auto-discovery from `.mimocode/agents/` confirmed
- [ ] Full gald3r install test completed

---

## 11. Relationship to OpenCode

MiMo-Code is a **fork of OpenCode** and is architecturally compatible. gald3r's existing
`g-skl-platform-opencode` knowledge is the starting point. Key additions over OpenCode:

| Feature | OpenCode | MiMo-Code |
|---|---|---|
| Cross-session memory | ❌ | ✅ (`MEMORY.md`, `checkpoint.md`) |
| Subagent orchestration | Basic | ✅ (full lifecycle, parallel, cancellable) |
| Dream/Distill | ❌ | ✅ (self-improvement loop) |
| Goal / stop condition | ❌ | ✅ (`/goal` with judge model) |
| Voice input | ❌ | ✅ (TenVAD + MiMo ASR) |
| Max Mode | ❌ | ✅ (parallel best-of-N with judge) |
| Default model | Provider agnostic | `mimo/mimo-v2.5-pro` |

**gald3r parity**: OpenCode parity target applies. MiMo-Code gains the OpenCode full parity
tier PLUS the memory/agent additions above. **Priority: ship MiMo support before competitors.**

---

## 12. Official Sources

- Docs: <https://mimo.xiaomi.com/mimocode>
- Agents: <https://mimo.xiaomi.com/mimocode/agents>
- GitHub: <https://github.com/XiaomiMiMo/MiMo-Code>
- MiMo model: <https://mimo.mi.com/>
- News: <https://www.neura.market/news/xiaomi-mimo-v2-5-pro-open-model-compiler-coding-benchmarks>

*Verified 2026-06-13 against GitHub README + mimo.xiaomi.com/mimocode docs.*
