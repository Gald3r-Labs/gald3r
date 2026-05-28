---
subsystem_memberships: [PLATFORM_INTEGRATION]
template_for: per-platform PLATFORM_SPEC.md (T1461–T1483)
---

# PLATFORM_SPEC_TEMPLATE.md

The standard document format every per-platform spec (T1461–T1483) MUST follow. Copy this file,
rename to `PLATFORM_SPEC.md` inside the platform's skill folder (or a per-platform docs location),
fill in every section, and mark unverified claims `❓` until tested.

> **Two authoring paths** — choose one at the top of the spec:
>
> - **UPDATE existing skill** — most platforms already ship `g-skl-platform-<name>/SKILL.md`.
>   Update that skill in place; this spec documents the verified findings.
> - **CREATE new skill** — `antigravity` (T1465) has NO existing `g-skl-platform-antigravity/`.
>   The spec author MUST first scaffold a new skill (use `@g-skill-new g-skl-platform-antigravity`
>   or copy the `g-skl-platform-cursor` structure), then complete this spec.

---

## Header / Metadata (fill before sections)

```yaml
platform: <name>            # e.g. windsurf
authoring_path: update | create   # "create" only for antigravity (T1465)
docs_url: https://...       # official documentation entry point (the SCAN_DOCS crawl target)
docs_url_secondary:         # optional: rules/MCP/hooks sub-pages
crawl_max_age_days: 7
vault_doc_path: research/platforms/<name>/
last_doc_scan: never
reference: g-skl-platform-cursor   # the platform compared against
status: ❓                   # ❓ unknown | ✅ healthy | ⚠️ partial | ❌ broken
```

> The `docs_url:` value is co-located in the platform's `g-skl-platform-<name>/SKILL.md`
> frontmatter. `g-skl-platform-monitor SCAN_DOCS` reads it to know what to crawl.

---

## 1. Folder Hierarchy

How the platform's config folder is structured. Show the tree (e.g. `.windsurf/rules/`,
`.windsurf/skills/`, …) and note which paths gald3r writes vs. which the platform owns.

## 2. AI Instruction File

What top-level instruction file the platform reads at session start
(`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.windsurfrules`, etc.). Note format, location, and
whether gald3r generates or merges into it.

## 3. Agents Support

How agent files (`g-agnt-*.md`) are discovered and loaded. Native concept? Manual selection vs.
auto-load? Format differences from the Cursor reference. `❓` if untested.

## 4. Skills Support

How skills (`g-skl-*/SKILL.md`) are discovered, loaded, and invoked. Folder-per-skill vs. flat?
Auto-loaded when relevant or invoked explicitly? Any naming/extension constraints.

## 5. Commands / Workflows

Slash commands, workflow files, or the platform's equivalent (`@g-*`, `/command`, workflow YAML).
Format, location, invocation syntax.

## 6. Hooks System

Lifecycle events the platform exposes (sessionStart, stop, preToolUse, beforeShellExecution, …),
the hook config format (`hooks.json`, settings entry, none), and the wiring mechanism. Note if the
platform has NO native hook system (then gald3r hooks run manually or via rules).

## 7. Rules / Memory

Persistent rules format and context-injection mechanism. Extension (`.md` vs Cursor's `.mdc`),
always-apply vs. on-demand, any token/size limits.

## 8. MCP Support

Yes/No. If yes: config format and location (`mcp.json`, settings, env), server discovery, timeout
behavior. If no: state it explicitly under Known Gaps.

## 9. Known Gaps vs. Cursor Reference

Explicit list of Cursor-reference features that do NOT work (or are untested) on this platform.
This is the honest-status section that feeds `PLATFORM_STATUS.md` and the capability matrix.
Use the decision tree in `g-skl-platform-cursor/SKILL.md`: capability either (a) belongs in
common `.gald3r_sys/`, (b) needs platform-specific config in `.gald3r_sys/platforms/.<name>/`,
or (c) is a documented gap here.

---

## Capability Summary (copy into PLATFORM_STATUS.md row)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| ❓ | ❓ | ❓ | ❓ | ❓ | ❓ |

Legend: ✅ verified working · ⚠️ partial / Cursor-generic · ❌ not supported · ❓ untested.

---

## Verification Evidence

Record HOW each capability was verified (install test, doc citation, manual run). Unverified
claims stay `❓`. A spec with all `✅` and no evidence is not complete.
