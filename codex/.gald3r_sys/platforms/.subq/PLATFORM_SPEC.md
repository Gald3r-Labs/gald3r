---
subsystem_memberships: [PLATFORM_INTEGRATION]
platform: subq
authoring_path: update
docs_url: https://subq.ai
docs_url_secondary:
  - https://subq.ai/introducing-subq
  - https://agentwiki.org/subq_code
crawl_max_age_days: 30
vault_doc_path: research/platforms/subq/
last_doc_scan: never
reference: g-skl-platform-cursor
status: ❓
---

# PLATFORM_SPEC.md — SubQ Code (Subquadratic Inc.)

SubQ Code is the **CLI coding agent** from Subquadratic Inc. (Miami, FL), built on the SubQ
subquadratic LLM (Subquadratic Sparse Attention, O(n)). Its headline capability is loading an
**entire codebase into a single context window** (1M tokens production, 12M research) — so it can
plan, execute, and review across a full repo "in one pass" with no chunking. Subquadratic positions
SubQ Code as a **long-context layer** that sits alongside existing tools, explicitly claiming
compatibility with **Claude Code, Codex, and Cursor**.

> **Authoring path: UPDATE** — `g-skl-platform-subq/SKILL.md` already ships (status: `stub`, T868).
> This spec records what is publicly verifiable and corrects nothing material in the skill (the
> skill is already honestly marked a stub). The SKILL.md remains the living reference; its new
> "Known Gaps" section points back here.

> **HONESTY NOTE — heavy ❓ is correct here.** SubQ Code is **private-beta / waitlist-only** as of
> May 2026 (confirmed via WebSearch 2026-05-26). There is **no public CLI, no public config-format
> documentation, and no published `.subq/` schema**. The only public surfaces are the
> marketing/announcement pages at https://subq.ai (model + product positioning) and a
> community knowledge base (agentwiki.org/subq_code). **Every gald3r-integration claim below
> about folders, instruction files, agents, skills, commands, hooks, rules, and MCP is
> UNCONFIRMED** — the platform's conventions are not yet public. `@g-platform-scan-docs subq` has
> **never** run (`last_doc_scan: never`) and cannot return authoritative config docs until the CLI
> ships publicly. **No fabrication**: where a convention is unknown it is marked ❓ and labeled
> "provisional / awaiting public CLI." gald3r has authored **no live SubQ Code deploy** in this repo.

---

## 1. Folder Hierarchy

**Status: ❓ provisional — config folder/path unconfirmed (no public CLI).**

gald3r ships a provisional deploy scaffold at `.gald3r_sys/platforms/.subq/` containing only
`subq_instructions.md` and `README.md` (documentation, no live config payload). The expected
project-config folder is `.subq/`, but this is a **placeholder**, not a verified convention:

```
<project-root>/
└── .subq/                  ← PROVISIONAL — folder name & contents unconfirmed (private beta)
    └── (instructions / config — format TBD on public CLI release)
```

Because SubQ Code claims **Cursor + Claude Code + Codex compatibility**, gald3r context most likely
already reaches SubQ Code today via the **existing root `AGENTS.md`** and the `.claude/` / `.cursor/`
surfaces — until the native `.subq/` convention is confirmed. gald3r writes **nothing** native to
SubQ Code yet (no `.subq/` payload is shipped).

**gald3r writes (today)**: nothing SubQ-native; relies on `AGENTS.md` + Cursor/Claude compatibility.
**SubQ Code owns**: the (unknown) config-folder name, instruction-file convention, and CLI surface.

---

## 2. AI Instruction File

**Status: ❓ provisional.**

The native SubQ Code instruction-file convention is **unknown** (no public docs). Expected pattern,
based on the existing SKILL.md and the Cursor/Claude/Codex compatibility claim: a root instruction
file (`AGENTS.md` / `CLAUDE.md` style) or a file inside `.subq/`. In the gald3r ecosystem the
canonical cross-platform instruction file is **`AGENTS.md`** (root), which SubQ Code likely honors
via its Claude Code / Codex compatibility. No SubQ-specific instruction file is shipped or verified.

---

## 3. Agents Support

**Status: ❓ unknown.**

No public documentation describes whether SubQ Code discovers agent-definition files. There is **no
evidence** of a `g-agnt-*.md` discovery directory analogous to `.cursor/agents/`. SubQ Code is a
single CLI coding agent; a multi-agent / agent-file-discovery model is **unconfirmed**. gald3r's
`g-agnt-*.md` files would, at best, be referenced indirectly via `AGENTS.md`. Marked ❓ — neither
supported nor disproven.

---

## 4. Skills Support

**Status: ❓ unknown.**

No public documentation describes a skills mechanism for SubQ Code. There is **no evidence** of a
`skills/<name>/SKILL.md` folder-per-skill discovery path. gald3r skills are not known to be ingested.
Marked ❓ pending the public CLI. (Contrast: the SubQ *value proposition* is whole-repo context, which
de-emphasizes skill/chunking machinery — but this is not the same as a verified skills API.)

---

## 5. Commands / Workflows

**Status: ❓ unknown.**

No public documentation describes slash commands, workflow files, or a `commands/` discovery
directory for SubQ Code. The known surface is a CLI invocation pattern only (illustrative, from the
SKILL.md — **command name unconfirmed**):

```bash
# Expected pattern only — NOT verified; public CLI not released
subq code --context /path/to/project "describe changes needed"
```

gald3r `g-*.md` command files are **not** known to be registered as SubQ Code commands. Marked ❓.

---

## 6. Hooks System

**Status: ❓ unknown (likely ❌ for gald3r `.ps1` hooks).**

No public documentation describes a lifecycle-event hook system for SubQ Code. There is **no evidence**
of a native hook wiring file (no `hooks.json` equivalent) and **no evidence** that gald3r's PowerShell
`g-hk-*.ps1` hooks would run. Absent a published hook taxonomy, gald3r hook integration is
**unconfirmed and presumed unavailable** until proven otherwise. Marked ❓ (recorded as a likely ❌).

---

## 7. Rules / Memory

**Status: ❓ unknown.**

No public documentation describes a persistent-rule format (no `.mdc` / `rules/` equivalent) or a
context-injection / memory mechanism for SubQ Code. The platform's defining feature — a 1M–12M token
context window — means an entire repo (and `.gald3r/` state) can be loaded directly, which may make a
dedicated rule-injection layer less necessary, **but no native rules/memory API is documented**.
gald3r `g-rl-*` rules have **no confirmed native injection point**; they would be folded into
`AGENTS.md` prose. Marked ❓.

---

## 8. MCP Support

**Status: ❓ unknown.**

No public documentation confirms Model Context Protocol support in the SubQ Code CLI. The **SubQ API**
is documented as **OpenAI-compatible** (`/v1/chat/completions`), which is an HTTP API contract, not an
MCP statement. Whether the SubQ Code *agent* consumes MCP servers (and via what config) is
**unconfirmed**. Marked ❓ pending the public CLI / docs.

---

## 9. Known Gaps vs. Cursor Reference

Compared to the Cursor reference (`g-skl-platform-cursor/PLATFORM_SPEC.md`), SubQ Code is
**almost entirely unverified** because it is private-beta with no public config docs:

1. **Private beta — no public CLI** ❓ — waitlist-only as of 2026-05; config conventions
   (folder name, instruction file, schemas) are **not published**. This gates every section below.
2. **Folder hierarchy ❓** — `.subq/` is a **provisional placeholder**, not a confirmed convention.
   gald3r ships docs-only scaffold (`subq_instructions.md`, `README.md`); **no live `.subq/` payload**.
3. **Instruction file ❓** — convention unknown; gald3r relies on root `AGENTS.md` via SubQ's claimed
   Claude Code / Codex / Cursor compatibility.
4. **Agents ❓** — no evidence of `g-agnt-*.md` discovery; single CLI agent, multi-agent model unconfirmed.
5. **Skills ❓** — no documented `SKILL.md` discovery path; gald3r skills not known to be ingested.
6. **Commands ❓** — only a CLI invocation pattern is hinted; gald3r `g-*.md` files not registered;
   exact command name (`subq code ...`) unconfirmed.
7. **Hooks ❓ (likely ❌)** — no documented hook system; gald3r `.ps1` hooks presumed not to run.
8. **Rules / Memory ❓** — no `.mdc` / `rules/` mechanism documented; rules would fold into `AGENTS.md`.
9. **MCP ❓** — API is OpenAI-compatible HTTP; CLI MCP support unconfirmed.
10. **SCAN_DOCS impossible today** — `last_doc_scan: never`. **Needs `@g-platform-scan-docs subq`
    once a public CLI + config docs exist.** Until then there is no authoritative doc surface to crawl
    (only marketing pages at subq.ai + community wiki). **No docs_url for CLI config exists yet.**
11. **No live gald3r deploy** — gald3r has exercised no SubQ Code install; the integration trigger is
    the public CLI release (see SKILL.md / T868).

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |

Legend: ✅ verified working · ⚠️ partial / capability-exists-but-gald3r-integration-unverified ·
❌ not supported · ❓ untested / unknown.

Overall platform `status: ❓` — **private beta, no public CLI/config docs; entirely unverified.**
This is the **honest** state: SubQ Code is a confirmed *real product* (Subquadratic Inc., $29M seed,
May 2026) but its gald3r-relevant config conventions are unpublished. Do **not** upgrade any cell off
❓ until the public CLI ships and `@g-platform-scan-docs subq` confirms real conventions.

---

## Verification Evidence

| Capability | How verified |
|---|---|
| Platform is real | WebSearch 2026-05-26: subq.ai/introducing-subq (SubQ subquadratic LLM); SubQ Code = CLI agent loading whole codebase in one pass; positions as long-context layer compatible with Claude Code, Codex, Cursor |
| Access status | WebSearch 2026-05-26: API, SubQ Code, SubQ Search are **private-beta, waitlist-only, no public pricing**; access by request at subq.ai |
| Model facts | Existing SKILL.md (T868): SSA O(n) attention, 1M token prod / 12M research, OpenAI-compatible `/v1/chat/completions`, SWE-Bench Verified 81.8% |
| Config folder | NOT verified — `.subq/` is provisional (override scaffold `.gald3r_sys/platforms/.subq/` ships docs only: subq_instructions.md, README.md) |
| Instruction file | NOT verified — convention unknown; gald3r relies on AGENTS.md + Cursor/Claude/Codex compatibility |
| Agents / Skills / Commands / Hooks / Rules / MCP | NOT verified — no public CLI config docs exist; all ❓ |
| Docs freshness | `last_doc_scan: never`; **no authoritative CLI-config docs URL exists** (only marketing pages + community wiki) — SCAN_DOCS deferred until public CLI release |
