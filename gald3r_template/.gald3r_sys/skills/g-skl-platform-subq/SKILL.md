---
name: g-skl-platform-subq
version: 0.1.0
status: stub
tier: adv
platform: subq
task: T868
created: 2026-05-09
token_budget: low
---

# g-skl-platform-subq — SubQ Code CLI (Subquadratic)

> **Status: STUB** — SubQ Code CLI is in private beta as of May 2026.
> This skill documents what is publicly known and will be updated once
> API access + CLI is confirmed (T868 Phase 1).

## What Is SubQ / Subquadratic?

**SubQ** is a first-generation subquadratic LLM from Subquadratic Inc. (Miami FL).
Key facts:

| Attribute | Value |
|---|---|
| Funding | $29M seed (May 5 2026) |
| Architecture | Subquadratic Sparse Attention (SSA) — O(n), not O(n²) |
| Context window | 1,000,000 tokens production; 12M research |
| API format | OpenAI-compatible (`/v1/chat/completions`) |
| SWE-Bench Verified | 81.8% (vs Claude Opus 4.6: 80.8%) |
| MRCR v2 @ 1M | 65.9% (vs Claude Opus 4.7: 32.2%) |
| Cost vs Claude Opus | ~300x cheaper at long context |
| Access | Private beta — https://subq.ai |

## Products (Private Beta)

1. **SubQ API** — REST API, full 1M token context
2. **SubQ Code** — CLI coding agent (loads entire codebases in one pass)
3. **SubQ Search** — long-context research tool

## gald3r Integration Status

| Component | Status |
|---|---|
| Provider stub in gald3r_throne | ✅ Added (T868) |
| Credential field (`SUBQUADRATIC_API_KEY`) | ⏳ Pending T868 Phase 2 |
| AI routing rule (>200K tokens → subquadratic) | ⏳ Pending T868 Phase 2 |
| Valhalla MCP provider entry | ⏳ Pending T868 Phase 3 |
| SubQ Code CLI install docs | ⏳ Pending public CLI release |

## SubQ Code CLI (stub)

```bash
# Install (pending public release — command may differ)
npm install -g subq-code
# or
brew install subq-code

# Usage (expected pattern)
subq code --context /path/to/project "describe changes needed"
```

SubQ Code explicitly supports Cursor and Claude Code integration — it is a natural 7th platform for gald3r (alongside Cursor, Claude Code, Gemini, Codex, OpenCode, GitHub Copilot).

## AGENTS.md / CLAUDE.md Equivalent

Unknown — check SubQ Code documentation when publicly available.
Expected: instruction file in project root or `.subq/` config directory.

## Integration Trigger (T868)

On receiving private beta API key:

1. Test `POST https://api.subq.ai/v1/chat/completions` with `Authorization: Bearer $SUBQUADRATIC_API_KEY`
2. Document actual base URL, streaming support, tool_calls support
3. Update this skill with verified connection details
4. Enable the `subquadratic` provider stub in gald3r_throne (T868 Phase 2)
5. Add routing rule: tasks with `estimated_tokens > 200_000` → prefer `subquadratic/subq-1m-preview`

## Long-Context Strategy

Once SubQ access is confirmed, the following gald3r features can skip chunking:
- `g-res-deep` 5-pass repo analysis (entire repo in one pass)
- `file_index` / vault search (may become optional at 1M ctx)
- `g-go-code` swarm buckets (full repo context without worktree overhead)

See T868 AC7 ADR note in `.gald3r/subsystems/llm_routing.md`.

---
*Updated: 2026-05-09 | Task: T868 | Access: private beta pending*
