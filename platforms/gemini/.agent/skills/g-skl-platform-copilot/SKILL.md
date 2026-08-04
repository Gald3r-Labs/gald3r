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

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
