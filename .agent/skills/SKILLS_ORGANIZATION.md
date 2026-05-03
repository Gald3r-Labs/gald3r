# Cursor Skills Organization Guide

## Overview
The `.cursor/skills/` directory supports **both flat and subfolder organization**. Cursor's Skill system will discover Skills in subdirectories automatically.

## Proven Evidence
Looking at existing Skills in this project:
- `document-skills/` contains subfolders: `docx/`, `pdf/`, `pptx/`, `xlsx/`
- Each subfolder has its own `SKILL.md`
- **All are recognized** by Cursor's Skill system

## Supported Organization Styles

### Style 1: Flat Structure (Simple Projects)
```
.cursor/skills/
├── skill-one/
│   └── SKILL.md
├── skill-two/
│   └── SKILL.md
└── skill-three/
    └── SKILL.md
```

**Best for**: < 20 Skills

### Style 2: Category-Based Subfolders (Recommended)
```
.cursor/skills/
├── GALD3R_system/
│   ├── gald3r-planning/
│   │   └── SKILL.md
│   ├── gald3r-qa/
│   │   └── SKILL.md
│   └── gald3r-task-management/
│       └── SKILL.md
├── integrations/
│   ├── atlassian-integration/
│   │   └── SKILL.md
│   ├── github-integration/
│   │   └── SKILL.md
│   └── web-tools/
│       └── SKILL.md
├── document_skills/
│   ├── docx/
│   │   └── SKILL.md
│   ├── pdf/
│   │   └── SKILL.md
│   └── pptx/
│       └── SKILL.md
└── code_quality/
    ├── gald3r-code-reviewer/
    │   └── SKILL.md
    └── computer-use-agent/
        └── SKILL.md
```

**Best for**: 20-100 Skills

### Style 3: Multi-Level Hierarchy (Large Projects)
```
.cursor/skills/
├── development/
│   ├── frontend/
│   │   ├── react-specialist/
│   │   └── ui-components/
│   ├── backend/
│   │   ├── api-design/
│   │   └── database-expert/
│   └── testing/
│       ├── unit-testing/
│       └── integration-testing/
├── operations/
│   ├── devops/
│   └── deployment/
└── business/
    ├── planning/
    └── documentation/
```

**Best for**: 100+ Skills

## Technical Details

### How Cursor Discovers Skills

Cursor scans for:
1. Directories under `.cursor/skills/`
2. Files named `SKILL.md` (case-sensitive)
3. **Recursively searches subdirectories**

### SKILL.md Requirements
Every Skill must have:
```yaml
---
name: skill-name
description: Brief description of skill functionality
triggers: [optional, list, of, trigger, phrases]
---

# Skill Name

[Skill content...]
```

### File Structure Example
```
.cursor/skills/category/skill-name/
├── SKILL.md                    # Required
├── rules.md                    # Optional
├── scripts/                    # Optional
│   ├── script1.py
│   └── requirements.txt
├── reference/                  # Optional
│   └── documentation.md
├── templates/                  # Optional
│   └── template.md
└── examples/                   # Optional
    └── example.md
```

## Best Practices

### 1. Consistent Category Names
Use clear, self-explanatory category names:
```
✅ integrations/
✅ GALD3R_system/
✅ document_skills/
❌ misc/
❌ stuff/
❌ other/
```

### 2. Shallow Hierarchy
Limit nesting to 2 levels maximum:
```
✅ .cursor/skills/category/skill-name/SKILL.md (2 levels)
❌ .cursor/skills/cat1/cat2/cat3/skill-name/SKILL.md (too deep)
```

### 3. Skill Name Clarity
Keep Skill folder names descriptive:
```
✅ gald3r-task-management/
❌ task-mgmt/
❌ rsrch/
```

### 4. Preserve Existing Structure
The `document-skills/` folder already uses subfolders - keep that structure:
```
document-skills/
├── docx/SKILL.md
├── pdf/SKILL.md
├── pptx/SKILL.md
└── xlsx/SKILL.md
```

### 5. Update Skill References
If Skills reference each other, update paths:
```markdown
Before:
See also: ../web-tools/SKILL.md

After (if moved to subfolder):
See also: ../../integrations/web-tools/SKILL.md
```

## Common Questions

### Q: Will subfolder organization break existing Skill invocations?
**A**: No. Cursor discovers Skills by scanning for `SKILL.md` files recursively. As long as the Skill structure is intact, it will work.

### Q: Do I need to update anything after reorganizing?
**A**: Only if:
- Skills reference each other with relative paths
- External documentation refers to specific Skill paths
- Scripts hardcode Skill paths

### Q: Can I mix flat and subfolder structures?
**A**: Yes. You can have some Skills in root and others in subfolders. Cursor will find all of them.

### Q: What's the performance impact of subfolders?
**A**: Negligible. Directory scanning is fast, and Cursor caches Skill locations.

### Q: Does this work for SubAgents too?
**A**: SubAgents are in `.cursor/agents/` and can also use subfolders.

## Proven Working Example

**Current Project Evidence**:
```
.cursor/skills/document-skills/
├── docx/SKILL.md         ✅ Works
├── pdf/SKILL.md          ✅ Works
├── pptx/SKILL.md         ✅ Works
└── xlsx/SKILL.md         ✅ Works
```

These Skills are in a subfolder and all work correctly.

---

**Last Updated**: 2026-01-29
**Status**: Tested and Confirmed Working
