---
name: pipeline-validation
description: Multi-agent QA gates for animation/videoΓÇöspecs, narrative, render readiness, asset handoff checks.
tags: [validation, qa, pipeline, multi-agent, quality-gates, production]
skill_group: "ai-video-tools"
skill_category: "AI Video Production"
---

# Pipeline Validation Gates

Multi-agent validation system for animation and video production pipelines. Ensures quality at each stage before proceeding.

## When to Use

- Before rendering final video output
- After completing a pipeline stage (modeling ΓåÆ rigging ΓåÆ animation ΓåÆ export)
- Validating asset handoff between pipeline stages
- QA checkpoints in automated workflows
- Pre-flight checks before cloud rendering

## Core Principle

```
Implementer Γëá Validator

The agent/person who created the work should NOT be the one
who validates it. Fresh eyes catch what familiarity misses.
```

## Validation Gates

### Gate 1: Spec Completeness
**When**: Before starting any production work
**Validates**: All required information is defined

```markdown
## Spec Completeness Check

- [ ] Target audience defined
- [ ] Goal/purpose stated
- [ ] Duration specified
- [ ] Aspect ratio set (16:9, 9:16, 1:1)
- [ ] Resolution defined (1080p, 4K)
- [ ] FPS specified (24, 30, 60)
- [ ] Style/tone described
- [ ] Audio requirements listed
- [ ] Deliverable formats listed
- [ ] Platform targets identified

**Result**: [PASS / FAIL ΓÇö list missing items]
```

### Gate 2: Asset Verification
**When**: Before composition/assembly
**Validates**: All required assets exist and meet specs

```markdown
## Asset Verification Check

### 3D Models
- [ ] All character GLBs present and loadable
- [ ] Triangle count within budget (see asset-optimization)
- [ ] Morph targets present (if animation requires)
- [ ] Animations embedded or linked

### Textures
- [ ] All textures present (diffuse, normal, roughness)
- [ ] Correct resolution for target
- [ ] Compressed format (WebP/KTX2)

### Audio
- [ ] Voiceover files present and correct duration
- [ ] Music track present
- [ ] Sound effects cataloged
- [ ] Audio levels normalized

### Fonts & Graphics
- [ ] All fonts loaded or embedded
- [ ] Logo files present (SVG preferred)
- [ ] Lower thirds / text overlays prepared

**Result**: [PASS / FAIL ΓÇö list missing assets]
```

### Gate 3: Narrative Consistency
**When**: After scene planning, before implementation
**Validates**: Story flow and visual continuity

```markdown
## Narrative Consistency Check

- [ ] Scene order makes logical sense
- [ ] Transitions between scenes are appropriate
- [ ] Visual style is consistent across scenes
- [ ] Audio continuity (no jarring cuts)
- [ ] Text/captions are readable and correctly timed
- [ ] Pacing matches content type (see explainer-video)
- [ ] CTA is clear and positioned correctly
- [ ] No continuity errors (character position, props)

**Result**: [PASS / FAIL ΓÇö list issues]
```

### Gate 4: Render-Readiness
**When**: Before final render
**Validates**: Technical readiness to render

```markdown
## Render-Readiness Check

- [ ] All imports resolve (no missing modules)
- [ ] No TypeScript/lint errors
- [ ] Preview renders without crash
- [ ] FPS stable in preview (no drops)
- [ ] Audio synced with visuals
- [ ] Safe zones respected (platform UI overlay)
- [ ] Correct output format configured
- [ ] Output file naming convention set
- [ ] Estimated render time acceptable

**Result**: [PASS / FAIL ΓÇö list blockers]
```

### Gate 5: Final QA
**When**: After render, before distribution
**Validates**: Output quality and correctness

```markdown
## Final QA Check

### Visual
- [ ] No visual glitches or artifacts
- [ ] Colors correct (no gamma issues)
- [ ] Text readable at target resolution
- [ ] No unintended blank frames
- [ ] Transitions smooth

### Audio
- [ ] Voiceover clear and correctly synced
- [ ] Music at appropriate level
- [ ] No audio pops or clicks
- [ ] Silence where expected (no noise floor)

### Technical
- [ ] File size within platform limits
- [ ] Correct resolution and aspect ratio
- [ ] Correct duration
- [ ] Correct codec and format
- [ ] Metadata correct (if applicable)

**Result**: [PASS / FAIL ΓÇö list defects]
```

## Gate Flow Diagram

```
[Spec] ΓåÆ Gate 1 ΓåÆ [Assets] ΓåÆ Gate 2 ΓåÆ [Scenes] ΓåÆ Gate 3 ΓåÆ [Build] ΓåÆ Gate 4 ΓåÆ [Render] ΓåÆ Gate 5 ΓåÆ [Ship]
  Γåæ         Γöé         Γåæ         Γöé          Γåæ         Γöé         Γåæ         Γöé          Γåæ         Γöé
  ΓööΓöÇ FAIL ΓöÇΓöÇΓöÿ         ΓööΓöÇ FAIL ΓöÇΓöÇΓöÿ          ΓööΓöÇ FAIL ΓöÇΓöÇΓöÿ         ΓööΓöÇ FAIL ΓöÇΓöÇΓöÿ          ΓööΓöÇ FAIL ΓöÇΓöÇΓöÿ
```

**On FAIL**: Fix issues, re-run the failed gate. Do NOT skip gates.

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **Blocker** | Cannot proceed | Fix immediately |
| **Major** | Quality unacceptable | Fix before next gate |
| **Minor** | Noticeable but not critical | Fix if time allows |
| **Note** | Suggestion for improvement | Optional |

## Integration with Our Pipeline

### SV Animation Pipeline Gates
```
[Character Spec] ΓåÆ Gate 1
[GLB Export] ΓåÆ Gate 2 (triangle count, morph targets, file size)
[Animation Setup] ΓåÆ Gate 3 (state machine, crossfade timings)
[R3F Scene] ΓåÆ Gate 4 (FPS check, no errors)
[Final Render] ΓåÆ Gate 5 (visual QA)
```

### Automated Gate Execution
```bash
# Run asset verification gate
gltf-transform inspect character.glb | check_budget.sh

# Run render-readiness gate
npx tsc --noEmit && npm run build

# Run FPS check
# (Use r3f-perf in headless mode or Playwright screenshot comparison)
```

### gald3r Integration
- Gates map to task status transitions:
  - Gate PASS ΓåÆ task moves to next status
  - Gate FAIL ΓåÆ task gets bug entry in BUGS.md
- Verification rule (32_GALD3R_verification.md) already enforces implementer Γëá verifier
