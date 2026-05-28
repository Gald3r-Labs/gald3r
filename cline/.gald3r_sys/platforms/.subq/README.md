# SubQ Code — gald3r Deploy Scaffold

**Config folder**: `.subq/` (provisional — confirmed on public CLI release)

This directory is the gald3r deploy scaffold for **SubQ Code** (Subquadratic Inc.).

Authoritative install + customization guide: **`g-skl-platform-subq`** (.gald3r_sys/skills/g-skl-platform-subq/SKILL.md).
Platform capability findings (honest, all unverified): **`PLATFORM_SPEC.md`** in this directory.

> **Status (T1277 / T1482 — provisional, all unverified):** SubQ Code is in private
> beta (T868). It is a confirmed real product (Subquadratic Inc., 1M-12M token context,
> OpenAI-compatible API) but has **no public CLI, no published config-format docs, and no
> confirmed `.subq/` schema**. See **`PLATFORM_SPEC.md`** in this directory for the full
> capability assessment (every section is honestly marked unverified) and
> **`subq_instructions.md`** for how gald3r context reaches SubQ Code today (root `AGENTS.md`
> + Claude Code / Cursor compatibility) and the exact completion trigger.
>
> A full config payload is intentionally deferred until the public CLI convention is
> confirmed — authoring it now would encode guesses. This scaffold therefore ships **no
> fabricated config surface and no `docs_url` for CLI config** (none exists yet): only
> documentation, the provisional `.subq/` placeholder, and reliance on `AGENTS.md`
> compatibility. Capability cells stay unverified until the public CLI ships and
> `@g-platform-scan-docs subq` confirms real conventions.

## Capability Summary (mirrors PLATFORM_SPEC.md)

| Hooks | Rules | Skills | Commands | MCP | Docs Fresh |
|---|---|---|---|---|---|
| unverified | unverified | unverified | unverified | unverified | unverified |

Overall platform status: **unverified** — private beta, no public CLI/config docs.
