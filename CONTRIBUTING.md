# Contributing to gald3r

Thank you for your interest in gald3r.

## Reporting Bugs

Use the [bug report template](https://github.com/wrm3/gald3r/issues/new?template=bug_report.yml) on GitHub Issues. The form asks for:

- Which AI platform or IDE you are using (Cursor, Claude Code, GitHub Copilot, Kiro, Windsurf, Cline, and 15+ others)
- The gald3r version from your `.gald3r/.identity` file
- Steps to reproduce, expected behavior, and actual behavior
- Relevant agent output or session logs if available

For security vulnerabilities, please do not open a public issue. Email the maintainer directly.

## Requesting Features

Use the [feature request template](https://github.com/wrm3/gald3r/issues/new?template=feature_request.yml). Describe:

- The problem you are trying to solve
- How you currently work around it
- What the ideal experience would look like

## Asking Questions

Use the [question template](https://github.com/wrm3/gald3r/issues/new?template=question.yml) or open a [GitHub Discussion](https://github.com/wrm3/gald3r/discussions) for usage questions, integration help, or general conversation.

## Code Contributions

gald3r is source-available under the [Fair Source License 1.1](LICENSE). **We are not accepting direct code contributions at this time.**

We review all feature requests and bug reports and may incorporate ideas into gald3r's development. If your idea is adopted, it will be implemented by the core team and credited in the release notes.

You are welcome and encouraged to:

- Build plugins, skills, extensions, or other works that interoperate with gald3r (the FSL license explicitly permits this)
- Share what you build in [Discussions](https://github.com/wrm3/gald3r/discussions)
- Report bugs and suggest improvements via issues

## How gald3r Is Developed

gald3r is built with gald3r. The source development repository uses gald3r's own task management, skill system, and quality gates to develop itself. Tasks are tracked in `.gald3r/TASKS.md`, acceptance criteria are written into individual task spec files, and the two-phase `@g-go-code` / `@g-go-review` gate is used for every feature.

The `gald3r` repository you are reading now is the installable consumer template, exported from the source repository on each release.

If you want to use gald3r in your own project, clone this repo and copy the contents into your project directory.