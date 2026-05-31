# SubQ Code Platform — gald3r Configuration Guide

**Platform**: SubQ Code (Subquadratic Inc. — long-context CLI coding agent)
**Config Folder**: `.subq/` (provisional — confirmed on public CLI release)
**gald3r Version**: 1.0.0
**Official Docs**: https://subq.ai (private beta)
**Authoritative skill**: `g-skl-platform-subq` (status: stub, T868)

---

## Status: Provisional (private beta)

SubQ Code is in **private beta** as of May 2026 (Subquadratic Inc., $29M seed, May 2026).
This is an intentionally provisional scaffold, not a placeholder gap: the platform's config
conventions are not yet publicly confirmed, so authoring a full config payload now would
encode guesses. This guide documents what is publicly known and the exact trigger for
completing the payload. Authoritative source: `g-skl-platform-subq` (T868).

What is known:

| Attribute | Value |
|-----------|-------|
| Architecture | Subquadratic Sparse Attention (SSA) — O(n) |
| Context window | 1,000,000 tokens (production) |
| API format | OpenAI-compatible (`/v1/chat/completions`) |
| Integration claim | Explicit Cursor + Claude Code compatibility |
| Access | Private beta — https://subq.ai |

---

## Expected Folder Layout (provisional)

```
<project-root>/
└── .subq/                  # Provisional — config file/path confirmed on public release
    └── (instructions / config — format TBD)
```

SubQ Code is expected to read an instruction file in the project root or a `.subq/` config
directory (CLAUDE.md / AGENTS.md pattern). Because SubQ Code claims Cursor + Claude Code
compatibility, the existing root `AGENTS.md` and `.claude/` surfaces likely already provide
gald3r context until the native convention is confirmed.

---

## gald3r Integration (provisional)

Until the public CLI lands, gald3r context reaches SubQ Code through its Claude Code /
Cursor compatibility:
- Root `AGENTS.md` — universal behavioral instructions.
- `.claude/` surfaces — if SubQ Code honors Claude Code compatibility as claimed.

## Completion Trigger (T868)

This scaffold is completed (full config + instructions payload) when:
1. SubQ Code public CLI is released and its config convention is confirmed.
2. `g-skl-platform-subq` is updated from `status: stub` with verified connection details.
3. The provisional `.subq/` layout above is replaced with the real config file(s).

---

## gitignore Decision (T1277 AC6)

No config files are shipped yet (private beta). If a future `.subq/config.*` holds an API
key (`SUBQUADRATIC_API_KEY`), the key belongs in an environment variable, not the committed
config — so the config remains **source**. No gitignore entry is needed for installed
projects at this time.

---

## Verification

```powershell
Test-Path .subq
subq --version 2>$null
```

(Both may be absent until SubQ Code is publicly available.)
