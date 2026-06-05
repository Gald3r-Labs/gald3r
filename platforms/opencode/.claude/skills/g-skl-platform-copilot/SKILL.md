---
name: g-skl-platform-copilot
description: Authoritative reference for GitHub Copilot customization in gald3r projects. Covers the .github/ tree (copilot-instructions.md, instructions/, prompts/, agents/, skills/, hooks/*.json), AGENTS.md + .claude/.agents skill reuse, Agentic Memory, surface fragmentation (VS Code / CLI / JetBrains / cloud agent), MCP, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/github_copilot/
vault_docs_url: https://docs.github.com/en/copilot
docs_url: https://docs.github.com/en/copilot/reference/customization-cheat-sheet
docs_url_secondary:
  - https://docs.github.com/en/copilot/reference/hooks-configuration
  - https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
  - https://docs.github.com/en/copilot/concepts/context/mcp
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native Copilot CLI lifecycle hooks in .github/hooks/*.json (sessionStart/userPromptSubmitted/preToolUse/postToolUse/sessionEnd/errorOccurred; preToolUse deny blocks; bash/.ps1; CLI GA, VS Code preview)"
  rules: "✅ .github/copilot-instructions.md (always-on) + .github/instructions/*.instructions.md (applyTo:) + reads AGENTS.md/CLAUDE.md/GEMINI.md; plus Agentic Memory"
  skills: "✅ Agent Skills (SKILL.md) discovered in .github/skills/, .claude/skills/, .agents/skills/ (cross-tool standard)"
  commands: "✅ prompt-file slash commands .github/prompts/*.prompt.md (VS Code only — NOT the CLI)"
  agents: "✅ custom agents .github/agents/AGENT-NAME.md + subagents (JetBrains GA; VS 2026 v18.4+)"
  mcp: "✅ native across IDE/CLI/cloud (STDIO/HTTP/SSE); config path differs per surface"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-platform-copilot

Activate for: setting up gald3r with GitHub Copilot (VS Code / Visual Studio / JetBrains / Copilot CLI / GitHub.com coding agent), authoring instructions/agents/skills/hooks/prompts, understanding the surface-fragmentation caveats, or verifying the Copilot gald3r install.

---

> Full 9-section breakdown + evidence URLs in `PLATFORM_SPEC.md` (this folder). **Status: ✅ near-full
> parity** — Copilot natively supports commands (prompt files), rules (custom instructions), agents,
> skills, hooks, and MCP, and reads `AGENTS.md` + discovers `.claude/skills/` + `.agents/skills/`, so
> gald3r's Claude-Code skill artifacts are largely reusable. Key caveat: **surface fragmentation** —
> a feature GA on one surface may be preview/absent on another. (Verified 2026-06-02 against the
> customization cheat sheet.)

## 1. Platform Overview

**GitHub Copilot** — GitHub's AI coding assistant across **VS Code**, **Visual Studio 2026 18.4+**,
**JetBrains**, the **Copilot CLI**, and the **Copilot coding agent on GitHub.com**. Each surface
supports a different subset of customization, so capabilities must be stated **per surface**.
Models are user-selectable per session (Anthropic / OpenAI / Google).

## 2. Config Layout

```
<project-root>/
├── AGENTS.md                          ← read by Copilot (nearest-in-tree wins); also CLAUDE.md / GEMINI.md
└── .github/
    ├── copilot-instructions.md        ← repo-wide always-on instructions (auto-loaded)
    ├── instructions/  *.instructions.md  ← path-scoped (frontmatter applyTo: "glob")
    ├── prompts/       *.prompt.md      ← prompt-file slash commands (VS Code only)
    ├── agents/        AGENT-NAME.md    ← custom agents (persona + tool restrictions)
    ├── skills/        <name>/SKILL.md  ← Agent Skills (YAML: name + description)
    └── hooks/         *.json           ← Copilot CLI lifecycle hooks (bash / PowerShell)

.claude/skills/ · .agents/skills/      ← Copilot ALSO discovers Agent Skills here  (cross-tool)
mcp.json (IDE) · ~/.copilot/mcp-config.json (CLI) · repo settings (cloud)  ← MCP per surface
.copilot/                              ← gald3r CONVENTION (NOT Copilot-native) — command ref docs
```

Copilot **also** discovers Agent Skills from `.claude/skills/` and `.agents/skills/` → **gald3r's
Claude-Code skill tree works as-is on Copilot.**

## 3. gald3r Integration

**Cheapest high-parity install: ship gald3r's `.claude/skills/` tree, plus a generated
`.github/copilot-instructions.md` (from always-apply rules) and `AGENTS.md`** — Copilot loads them
natively. Map `g-agnt-*` → `.github/agents/AGENT-NAME.md`, `g-rl-*` → `copilot-instructions.md`
(or `.github/instructions/` for path-scoped, adv tier), `g-hk-*.ps1` → `.github/hooks/*.json`
(PowerShell variant, CLI surface), `@g-*` → `.github/prompts/*.prompt.md` (VS Code surface).
Distribute org-wide via `.github-private`; discover via `github/awesome-copilot`.

### Verify
```powershell
Test-Path .github/copilot-instructions.md   # always-on rules (generate_copilot_instructions.ps1 if missing)
Test-Path .claude/skills                     # Agent Skills (Copilot discovers cross-tool)
Test-Path .github/agents ; Test-Path .github/prompts ; Test-Path .github/hooks
```

## 4. Common Pitfalls

- **Surface fragmentation** is the #1 trap: prompt-file slash commands are **VS Code-only** (NOT the
  CLI — issues #618/#1113); custom agents need **VS 2026 v18.4+**; hooks are **CLI-GA / VS Code-preview**.
  Always check the surface before claiming a capability is universal.
- Instruction file: Copilot reads **`AGENTS.md`** directly (nearest-in-tree wins) **plus** its native
  `.github/copilot-instructions.md` — it does NOT require a `CLAUDE.md` import the way Claude Code does.
- Skills are **multi-path** (`.github/skills/` + `.claude/skills/` + `.agents/skills/`) — reuse the
  existing `.claude/skills/` tree; do NOT duplicate into `.github/skills/`.
- Hooks fire **only during an active agent session** (CLI/cloud) — they are NOT git hooks / CI /
  Actions. Plain `git commit` is unaffected, so session-start/pre-commit gates do not run on commits.
- **Agentic Memory** (agent-authored repo/user facts) is a distinct dynamic store — do not conflate
  it with the static `copilot-instructions.md`. It is Copilot-managed, not gald3r-writable.
- MCP config path differs per surface (`mcp.json` / `~/.copilot/mcp-config.json` / repo settings) —
  not single-path portable.
- Use `.md` (not Cursor's `.mdc`) for instruction/rule files — parity sync swaps the extension.

## 5. Capability Summary

| Feature | Status | Notes |
|---|---|---|
| Hooks (`g-hk-*.ps1`) | ✅ | `.github/hooks/*.json`; sessionStart/userPromptSubmitted/preToolUse/postToolUse/sessionEnd/errorOccurred; preToolUse `deny` blocks; CLI GA, VS Code preview |
| Skills (`g-skl-*/SKILL.md`) | ✅ | Agent Skills standard; discovered in `.github/skills/` / `.claude/skills/` / `.agents/skills/` |
| Agents (`g-agnt-*.md`) | ✅ | custom agents `.github/agents/AGENT-NAME.md` + subagents (JetBrains GA; VS 2026 v18.4+) |
| Commands (`@g-*`) | ✅ | prompt-file slash commands `.github/prompts/*.prompt.md` — **VS Code only**, not the CLI |
| Rules (`g-rl-*`) | ✅ | `.github/copilot-instructions.md` (always-on) + `.github/instructions/` (`applyTo:`); reads `AGENTS.md`; plus Agentic Memory |
| MCP | ✅ | native IDE/CLI/cloud (STDIO/HTTP/SSE); `mcp.json` / `~/.copilot/mcp-config.json` / repo settings |

Full assessment + evidence in `PLATFORM_SPEC.md`. Re-verify on the next `@g-platform-scan-docs copilot` (crawl_max_age_days: 7).
