---
name: gald3r
description: "gald3r framework conventions -- task management, bug tracking, code standards, and project coordination"
---

# gald3r Project Skill

## Task Management
- Tasks: .gald3r/TASKS.md and .gald3r/tasks/
- Bugs: .gald3r/BUGS.md and .gald3r/bugs/
- Constraints: .gald3r/CONSTRAINTS.md (check before completing any task)
- Plan: .gald3r/PLAN.md

## Status Emoji
- [📋] pending
- [🔄] in progress
- [🔍] awaiting verification
- [✅] done

## Commit Format
`
feat(scope): description

Task: #NNN
`
"@

Set-Content -Path "G:\gald3r_ecosystem\gald3r_templates_repos\gald3r\trae\.trae\rules\gald3r.md" -Value @"
# gald3r Project Rules

Always check .gald3r/CONSTRAINTS.md before completing any task.
Reference task IDs in all commits using Task: #NNN format.
