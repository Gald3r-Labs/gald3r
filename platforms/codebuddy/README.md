# CodeBuddy — gald3r Template

**gald3r** for **CodeBuddy** (Tencent Cloud AI coding assistant)

---

## What is CodeBuddy?

[CodeBuddy](https://www.codebuddy.ai/) is Tencent Cloud's AI programming tool. It comes in three forms:

- **CodeBuddy IDE** — standalone AI-first editor
- **CodeBuddy Plugin** — VS Code / JetBrains extension
- **CodeBuddy Code** — terminal CLI (`npm install -g @tencent-ai/codebuddy-code`)

Supports DeepSeek + Tencent Hunyuan models. 200+ languages. MCP integration.

---

## gald3r Compatibility

**Tier 1 — Full Native Compatibility**

CodeBuddy has a native `SKILL.md` system at `.codebuddy/skills/` that uses the **exact same format** as gald3r. This is one of the highest-compatibility platforms in the gald3r ecosystem.

---

## Quick Start

### New Project

```bash
# Install CodeBuddy CLI
npm install -g @tencent-ai/codebuddy-code

# Clone this template
git clone https://github.com/wrm3/gald3r
cd gald3r/codebuddy

# Copy to your project
cp -r .codebuddy/ /path/to/your/project/

# Launch CodeBuddy in your project
cd /path/to/your/project
codebuddy
```

### Add to Existing Project

```bash
# From the gald3r repo, copy the .codebuddy folder
cp -r gald3r/codebuddy/.codebuddy/ /path/to/your/project/
```

---

## What's Inside

```
codebuddy/
+-- .codebuddy/
    +-- skills/
        +-- g-skl-status/SKILL.md       <- session context loader
        +-- g-skl-tasks/SKILL.md        <- task management
        +-- g-skl-bugs/SKILL.md         <- bug tracking
        +-- g-skl-review/SKILL.md       <- code review
        +-- g-skl-medic/SKILL.md        <- health check
        +-- [... all gald3r skills ...]
```

### Invoking Skills

- Press `/` in CodeBuddy to open the skill picker
- Type `/<skill-name>` to invoke directly (e.g., `/g-skl-status`)
- Skills auto-invoke based on context

---

## Supported Regions

- **International**: Google/GitHub login — Gemini, GPT, Claude models
- **China**: WeChat login — DeepSeek, Hunyuan models

---

## Learn More

- [CodeBuddy Documentation](https://www.codebuddy.ai/docs/ide/Introduction)
- [CodeBuddy Skills System](https://www.codebuddy.ai/docs/cli/skills)
- [gald3r Framework](https://github.com/wrm3/gald3r)
