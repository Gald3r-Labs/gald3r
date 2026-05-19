---
name: g-skl-platform-kiro-cli
description: Authoritative reference for Kiro CLI (Amazon's terminal agent variant) customization in gald3r projects. Covers .kiro/steering/ for CLI sessions, CLI-specific config, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/kiro-cli/
vault_docs_url: https://kiro.dev/docs/cli
token_budget: low
---

# g-skl-platform-kiro-cli

Activate for: setting up gald3r with Kiro CLI (terminal variant), configuring CLI steering, understanding differences from Kiro IDE, or verifying Kiro-CLI gald3r integration.

---

## 1. Platform Overview

**Kiro-CLI** is the terminal agent variant of Amazon's Kiro platform. It shares the `.kiro/` directory convention with Kiro IDE but operates in a headless CLI mode suitable for CI/CD and scripted workflows. It reads steering files from `.kiro/steering/`.

- **Steering**: `.kiro/steering/` — same as Kiro IDE (shared config directory)
- **CLI mode**: Headless task execution, suitable for automation
- **Specs**: Reads `.kiro/specs/` for context, same as IDE variant
- **AWS integration**: Native AWS service awareness via environment credentials

**gald3r target tier**: CLI agent. Shares `.kiro/` dir with Kiro IDE; steering files work for both.

---

## 2. Config File Layout

```
<project-root>/
└── .kiro/
    ├── steering/                   ← Injected into all Kiro sessions (IDE + CLI)
    │   ├── gald3r.md               ← gald3r task management context
    │   └── product.md              ← Product context
    ├── specs/                      ← Feature specs (shared with IDE)
    └── hooks/                      ← Automation hooks
```

**Same directory as Kiro IDE** — if you have `g-skl-platform-kiro` set up, Kiro-CLI shares the same config.

---

## 3. gald3r Integration

### Install

```bash
node bin/install.js --only kiro-cli
```

Creates `.kiro/steering/gald3r.md` (same file as Kiro IDE install; idempotent).

### CLI-Specific Usage

```bash
# Run Kiro CLI with specific task context
kiro run --steering .kiro/steering/gald3r.md "implement feature X per .gald3r/tasks/task1042..."

# Non-interactive (CI mode)
kiro --no-interactive --spec .kiro/specs/feature-x/requirements.md
```

### CI Integration

```yaml
# .github/workflows/kiro-task.yml
- name: Run Kiro CLI task
  run: kiro run --task "fix bug per .gald3r/bugs/bug042_*.md"
  env:
    AWS_DEFAULT_REGION: us-east-1
```

---

## 4. Verification

```bash
kiro --version 2>/dev/null || echo "Kiro CLI not detected"
Test-Path .kiro/steering
node bin/install.js --list --target .
```

---

## 5. Common Pitfalls

- Kiro-CLI and Kiro IDE share `.kiro/` — installing for one configures the other automatically
- CLI mode requires AWS credentials for Amazon Q / Bedrock model access
- Headless mode may not read all steering files — verify with `kiro --debug` output
