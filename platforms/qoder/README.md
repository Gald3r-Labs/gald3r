# Qoder (Alibaba) + gald3r

**Tier 2 — Community Supported**

[Qoder](https://qoder.com) is Alibaba's agentic coding platform with 100,000-file codebase retrieval, auto-generated Repo Wiki, Quest Mode for autonomous task execution, and a project-specific rules system at `.qoder/rules/`. Available as a standalone IDE (macOS/Windows) and JetBrains plugin.

## Why Use Qoder?

- **100k file context**: Deep codebase understanding at massive scale
- **Quest Mode**: Autonomous long-running task execution via spec-driven workflows
- **Repo Wiki**: Auto-generated architecture documentation
- **Persistent Memory**: Global + project-specific memory
- **Multi-model**: Auto-selects from Claude, GPT, Gemini, Qwen
- **MCP**: Full MCP integration

## Quick Start (New Project)

1. Download **Qoder** from [qoder.com](https://qoder.com) (macOS or Windows) or install the JetBrains plugin
2. Copy the `qoder/` folder contents to your project root
3. In Qoder Settings > Rules, import `.qoder/rules/gald3r.md` as an **Always Apply** rule

## What's Inside

```
qoder/
  .qoder/
    rules/
      gald3r.md           # Always Apply rule with gald3r conventions
  README.md               # This file
```

## Rules Configuration

In Qoder Settings > Rules > Add:
- **Name**: `gald3r`
- **Type**: Always Apply
- The `.qoder/rules/gald3r.md` file is auto-loaded from the project directory

## Quest Mode + gald3r Tasks

Qoder's Quest Mode accepts specification documents. gald3r task files (`.gald3r/tasks/taskNNN_*.md`) work directly as Quest specs — the acceptance criteria and implementation steps map naturally to Qoder's workflow.

## Documentation

- **Primary**: [docs.qoder.com](https://docs.qoder.com)
- **Rules docs**: [docs.qoder.com/user-guide/rules](https://docs.qoder.com/user-guide/rules)
