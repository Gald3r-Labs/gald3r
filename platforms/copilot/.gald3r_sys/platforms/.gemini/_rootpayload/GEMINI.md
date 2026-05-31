# Gemini CLI Project Instructions

> This file is read by Gemini CLI (gemini command). Keep it focused and concise.

## Imported Context
<!-- @./.gemini/context/*.md if you add context files -->

## Operating Rules
- Read PLAN.md before broad architectural changes
- Update TASKS.md when work is completed  
- Follow patterns in .agent/rules/ for project conventions
- Prefer small, reviewable changes

## gald3r Integration
Skills and agents live in .agent/ (separate from .gemini/):
- .agent/skills/ - gald3r skill files
- .agent/agents/ - gald3r agent definitions
- .agent/rules/ - project rules

## Commands
Native Gemini CLI commands are in .gemini/commands/*.toml.
