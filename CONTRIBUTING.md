# Contributing to gald3r

Thank you for your interest in improving gald3r.

## Reporting Bugs

Use the [bug report template](https://github.com/wrm3/gald3r/issues/new?template=bug_report.yml) on GitHub Issues. The form asks for:

- Which IDE you are using (Cursor, Claude Code, Gemini, Codex, OpenCode)
- The gald3r version from your `AGENTS.md` or `.gald3r/.identity`
- Steps to reproduce, expected behavior, and actual behavior
- Relevant hook or session logs if available

For security vulnerabilities, please do not open a public issue. Email the maintainer directly.

## Requesting Features

Use the [feature request template](https://github.com/wrm3/gald3r/issues/new?template=feature_request.yml). Describe:

- The problem you are trying to solve
- How you currently work around it
- What the ideal experience would look like

Features that work across all five IDEs (not Cursor-only) are prioritized.

## Suggesting Improvements

Open a plain issue or start a discussion if you have ideas that do not fit neatly into a bug or feature request. Examples:

- A new skill that would benefit most projects
- A documentation gap
- An inconsistency across IDEs
- A new platform gald3r should support

## How gald3r Is Developed

gald3r is built with gald3r. The source development repository (`gald3r_dev`) uses gald3r's own task management, skill system, and quality gates to develop itself. Tasks are tracked in `.gald3r/TASKS.md`, acceptance criteria are written into individual task spec files, and the two-phase `@g-go-code` / `@g-go-review` gate is used for every feature.

The `gald3r` repository you are reading now is the installable consumer template. It is exported from `gald3r_template_full/` in the `gald3r_dev` source repository on each release.

This means:

- If you want to use gald3r in your own project, you are in the right place. Clone this repo and copy the contents into your project.
- If you want to contribute changes to the framework itself, open an issue describing what you want to change. Accepted contributions are integrated into the `gald3r_dev` source and shipped in the next release.

## Questions

Open a [GitHub Discussion](https://github.com/wrm3/gald3r/discussions) for usage questions, integration help, or general conversation about AI-driven development workflows.
