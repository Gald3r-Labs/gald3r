# Kiro CLI Platform — gald3r Configuration Guide

**Platform**: Kiro CLI (Amazon's terminal agent variant of Kiro)
**Config Folder**: shared `.kiro/` (steering / specs / hooks)
**gald3r Version**: 1.0.0
**Official Docs**: https://kiro.dev/docs/cli
**Config Surface**: `.kiro/steering/` (shared with Kiro IDE)
**Authoritative skill**: `g-skl-platform-kiro-cli`

---

## Folder Layout

Kiro CLI **shares the `.kiro/` directory with Kiro IDE** — there is no separate config tree.
Installing for either variant configures both (idempotent).

```
.kiro/
├── steering/                   # Injected into all Kiro sessions (IDE + CLI)
│   ├── gald3r.md               # gald3r task management context (shared)
│   └── product.md              # Product context (shared)
├── specs/                      # Feature specs (shared with IDE)
└── hooks/                      # Automation hooks
```

> The canonical steering files live under `.gald3r_sys/platforms/.kiro/steering/`. This
> `.kiro-cli/` scaffold carries the CLI-specific guidance only; it does **not** duplicate
> the steering files (they are shared via `.kiro/`).

---

## What Makes Kiro CLI Unique

### Headless / CI Mode
Kiro CLI runs Kiro's spec-driven model headlessly — suitable for CI/CD and scripted
workflows. It reads the same `.kiro/steering/` files as the IDE.

```bash
# Run a task with gald3r context
kiro run --steering .kiro/steering/gald3r.md "implement per .gald3r/tasks/task1042_*.md"

# Non-interactive (CI)
kiro --no-interactive --spec .kiro/specs/feature-x/requirements.md
```

### AWS Credentials
CLI mode needs AWS credentials for Amazon Q / Bedrock model access (set
`AWS_DEFAULT_REGION` etc. in the environment).

---

## gald3r Naming Conventions

| Component | Surface |
|-----------|---------|
| Skills | served from root `skills/` |
| Agents | (none — Kiro agent reads steering + specs) |
| Commands | (none — `kiro` CLI) |
| Rules | `.kiro/steering/*.md` (shared with Kiro IDE) |

---

## Config Files Shipped

- This guide. The steering files are shared from the `.kiro/` scaffold
  (`g-skl-platform-kiro`) — Kiro CLI reads them directly.

---

## gitignore Decision (T1277 AC6)

Identical to Kiro IDE: `.kiro/steering/*.md` are **source** — keep them tracked. Headless
run logs are written outside the project; no generated project output dir needs gitignoring.

---

## Verification

```powershell
kiro --version
Test-Path .kiro/steering
```

---

## Common Pitfalls

- Kiro CLI and Kiro IDE share `.kiro/` — installing one configures the other.
- CLI mode requires AWS credentials for model access.
- Headless mode may not read all steering files — verify with `kiro --debug`.
