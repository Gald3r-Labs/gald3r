---
name: g-skl-cli-opencode
description: OpenCode CLI (opencode command) — stub. OpenCode is an emerging AI coding tool from sst.dev. Full documentation pending stable release.
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

# g-skl-cli-opencode — OpenCode CLI

> **Status: Stub** — OpenCode CLI documentation is pending a stable release.
> This file will be populated via `@g-ingest-docs` once stable docs are available.

> **Not to be confused with**: The **OpenAI Codex CLI** (`codex` binary) — see `g-skl-cli-codex` for that tool.

Reference docs will live in: `{vault_location}/research/platforms/opencode/` once populated via `@g-ingest-docs`.

## What is OpenCode?

OpenCode is an open-source, terminal-first AI coding tool by the sst.dev team (`opencode` binary).
Its CLI interface is under active development.

- GitHub: https://github.com/sst/opencode
- Not the same product as OpenAI Codex CLI (`codex` binary)

## Current State

- `.opencode/` configuration directory is part of the gald3r 10-target set
- `opencode.json` in project root holds model and provider configuration
- Full CLI documentation is not yet stable

## When Docs Are Available

Run `@g-ingest-docs` targeting the OpenCode documentation URL to populate:
`{vault_location}/research/platforms/opencode/`

This stub will be replaced with full CLI guidance at that time.

## See Also

- `g-skl-cli-codex` — OpenAI Codex CLI (`codex` command) — fully documented
- `g-skl-cli-cursor` — Cursor CLI (`agent` command)
- `g-skl-cli-claude` — Claude Code CLI (`claude` command)
- `g-skl-cli-gemini` — Gemini CLI (`gemini` command)

## Vault Reference

`{vault_location}/research/platforms/opencode/` — ready for content.
