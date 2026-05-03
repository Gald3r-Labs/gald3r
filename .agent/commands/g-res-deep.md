---
description: Deep analysis of a captured repo, URL, or vault note — produces a structured recon report. Agents are reporters; humans are editors.
---
# g-res-deep

Activates `g-skl-res-deep`. Performs a 5-pass deep analysis of any external repository or
captured vault content and produces `vault/research/recon/{slug}/` — no `.gald3r/` writes
until you run `@g-res-apply`.

> **Replaces**: `@g-reverse-spec` (deprecated alias — prints warning, then calls this)

```
@g-res-deep ANALYZE https://github.com/user/repo
@g-res-deep ANALYZE vault:research/repos/owner__repo.md
@g-res-deep RESUME user__repo
@g-res-deep APPLY user__repo
@g-res-deep APPLY --dry-run user__repo
@g-res-deep STATUS user__repo
```

**Passes**: Skeleton → Module Map → Feature Scan → Deep Dives → Synthesis

**Reporter rule**: Document everything. Never filter by "gald3r already has this."

## Output

Writes to `vault/research/recon/{slug}/`:
- `01_skeleton.md` — repo structure + tech fingerprint
- `02_module_map.md` — module/component decomposition
- `03_feature_scan.md` — raw feature inventory
- `04_FEATURES.md` — structured feature list (input for `@g-res-apply`)
- `05_synthesis.md` — adoption recommendations

## Clean Room Boundary

These commands support clean-room research and reverse-spec work. Capture/recon may observe and summarize source behavior, interfaces, workflows, data shapes, and architectural patterns; generated gald3r artifacts must use original wording and local architecture terms, not copied source code, docs prose, prompts, tests, or unique strings. Keep source URL, license, and capture provenance in recon notes; treat source file paths as traceability, not implementation instructions. Adoption requires human approval through `@g-res-review` / `@g-res-apply`.

## See Also

- `@g-recon-repo` — Lightweight capture first (then `--deep` or this command)
- `@g-res-review` — Review existing recon reports
- `@g-res-apply` — Apply approved features to .gald3r/
