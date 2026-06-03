**Released:** 2026-05-28
**Version:** 1.7.0
**Type:** Minor -- new features, no breaking changes

---

## Highlights

### 34 AI Coding Tools -- Full Sweep
11 new platforms added in this release: Kimi Code (Moonshot AI), TRAE (ByteDance),
Qoder (Alibaba), Amp Code (Sourcegraph), Continue, Void Editor, Deep Code (DeepSeek),
Kilo Code, Hermes (Nous Research), CodeBuddy (Tencent), AstrBot. All 34 platforms
verified QA-passing.

### g-go-go Coding Swarm Fix
`g-go-go` Phase 1 now explicitly invokes `g-go-code-swarm` (N parallel coders) instead
of running one coder at a time. Phase 2 was already parallel (review swarm) -- Phase 1
was silently sequential. This was the root cause of the framework feeling slow over the
past week. Added `--no-code-swarm` opt-out flag.

### Context-Aware Throttle ON by Default
`--context-aware` is now the default. Proactively reduces N under context pressure
instead of triggering a `CONTEXT WINDOW PANIC` stop. `--no-context-aware` to opt out.

### Platform Restructure (T1522)
All 34 platform templates now live at repo root (`cursor/`, `claude/`, etc.) -- no more
`platforms/<name>/` nesting. Each folder is ready to drop directly into your project.

---

## Full Change List

See [CHANGELOG.md](../CHANGELOG.md) `## [1.7.0]` section for the complete detailed list.

---

## Install / Upgrade

Pick your platform folder and copy its contents to your project root:

```bash
# Example for Cursor
cp -r cursor/ /your/project/
```

For a fresh install see [instructions_new_project.md](../instructions_new_project.md).
For upgrading an existing install see [instructions_existing_project.md](../instructions_existing_project.md).

---

## Platform Count

| Tier | Count | Platforms |
|---|---|---|
| Tier 1 (Fully Supported) | 11 | Cursor, Claude Code, Copilot, Windsurf, Cline, Roo, Codex, CodeBuddy, Amp, Continue, Kimi |
| Tier 2 (Community) | 11 | Aider, Augment, Goose, Warp, OpenHands, Kiro, Kiro CLI, Junie, Replit, Gemini, Kilo Code, Qoder |
| Tier 3 (Experimental) | 9 | Mistral, Antigravity, OpenClaw, Qwen, SubQ, DeepCode, Hermes, AstrBot, Void, TRAE |
| **Total** | **34** | |