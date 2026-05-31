# Void Editor + gald3r

**Tier 3 — Experimental**

> **Note**: Void's core development team paused active development in early 2026. The last release (v1.3.4) remains functional. The Apache 2.0 codebase is community-maintained. This template is provided for Void users who need privacy-first local model routing.

[Void](https://voideditor.com) is an open-source VS Code fork that sends prompts directly to your LLM provider with no proprietary backend — a privacy-first alternative to Cursor.

## Why Use Void?

- **Zero backend**: Your code goes directly from editor to model provider (OpenAI, Anthropic, Ollama, DeepSeek, etc.)
- **Privacy-first**: No data routed through Sourcegraph, Cursor, or any middleman
- **Full VS Code compatibility**: All extensions, themes, and keybindings transfer
- **Free + open source**: Apache 2.0 licensed, Y Combinator backed
- **Local models**: Full Ollama support (Llama, Qwen, DeepSeek, Gemma)

## Quick Start (New Project)

1. Download Void from [voideditor.com](https://voideditor.com) or [GitHub releases](https://github.com/voideditor/void/releases)
2. Copy the `void/` folder contents to your project root
3. Open your project in Void

## What's Inside

```
void/
  .cursorrules        # AI project guidance (Void reads .cursorrules)
  README.md           # This file
```

## gald3r Compatibility

Void reads `.cursorrules` for AI guidance. Place your project conventions there. Void does not support a skill system, so gald3r framework conventions are embedded directly in the rules file.

## Limitations

- Development paused — no new features expected
- No skill/command/hook system
- Rules via `.cursorrules` only (no Cursor-style `.cursor/rules/` folder)
- Community forks may restore active development

## Documentation

- **Primary**: [voideditor.com](https://voideditor.com)
- **Source**: [github.com/voideditor/void](https://github.com/voideditor/void)
