---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
Scan a platform's official docs for breaking changes: $ARGUMENTS

## What This Command Does

Crawls the official documentation of the named platform and diffs against the last crawl,
surfacing sections that changed since the previous scan so they can be reviewed for gald3r
compatibility impact. Delegates to `g-skl-platform-monitor` operation `SCAN_DOCS`, then drives
the T514/T515 freshness consumers end-to-end: crawl-export (T646) → `gald3r platform refresh` proposal
→ human-accept → `gald3r platform status --apply` regen.

## Delegates To

- Skill: `g-skl-platform-monitor` → `SCAN_DOCS`
- Crawl: `g-skl-crawl` / `g-skl-recon-docs` on the platform's `docs_url:`
- Exporter: `scripts/platform_crawl.py` (T646 — host-side crawl snapshot + ledger)
- Consumers: `gald3r platform refresh` (T514) and `gald3r platform status` (T515)
- Agent: `g-agnt-platformer`

## Workflow

1. Activate `g-agnt-platformer`.
2. Read `docs_url:` from `g-skl-platform-<platform>/SKILL.md` frontmatter.
3. Run `g-skl-platform-monitor SCAN_DOCS <platform>` — crawls the URL, stores results under
   `{vault_location}/research/platforms/<platform>/`, diffs against the prior snapshot.
4. **Export the crawl snapshot (T646).** Produce the host-side JSON inputs the freshness
   consumers read:
   ```
   python scripts/platform_crawl.py --source db --db-url "$GALD3R_DATABASE_URL" \
       --platform <platform> --crawl-snapshot <platform>_docs.json --crawl-ledger ledger.json
   ```
   No live DB available (or offline smoke test)? Use `--source sample` instead — it writes a
   small, clearly-labeled fixture snapshot so the rest of the pipeline can still be exercised.
5. **Run the spec-refresh proposal (T514, GAP A) — dry-run, never blind-applied.**
   ```
   gald3r platform refresh --platform <platform> \
       --crawl-snapshot <platform>_docs.json --crawl-ledger ledger.json
   ```
   Surface the printed proposal for **human review**: the `*.proposed` draft, the
   "what changed and why" summary, and any `[needs-review]` capability-cell disagreements
   between the crawled docs and the curated `PLATFORM_SPEC.md`. This step is dry-run by
   default and NEVER auto-flips a curated cell — disagreements are judgment calls for a human,
   not the model (model-for-judgment-only; g-rl-38).
6. **STOP for human accept.** Do not proceed to step 7 until the operator has reviewed the
   proposal and explicitly accepted it (editing `PLATFORM_SPEC.md` capability cells by hand
   where flagged `[needs-review]`, if warranted).
7. **On accept, land the mechanical stamp and regenerate STATUS.**
   ```
   gald3r platform refresh --platform <platform> \
       --crawl-snapshot <platform>_docs.json --crawl-ledger ledger.json --apply
   gald3r platform status --apply --crawl-ledger ledger.json
   ```
   `--apply` on `gald3r platform refresh` lands ONLY the mechanical `last_doc_scan` stamp — capability
   cells are never auto-applied, matching step 5's human-review gate.
8. **Report the matrix cross-check.** Run
   `check_platform_status.py --generate-matrix` and count the `WARN: Matrix says … but STATUS
   says …` lines it prints — this is the "matrix cross-check warning count" the operator should
   see. Expect **0** after a clean accept + regen (T513's whole point: STATUS and the matrix can
   never legitimately disagree once both are regenerated from the same specs).
9. Updating `last_doc_scan` in `.gald3r/PLATFORM_STATUS.md` is handled by step 7's regen — no
   manual edit needed.

## Usage Examples

```
@g-platform-scan-docs antigravity     # high-priority: relaunched with breaking changes
@g-platform-scan-docs cursor
```

## Guardrails

- **Human-accept gate is mandatory.** Step 6 is a hard stop — the command never runs step 7
  without an explicit human accept. The model classifies/summarizes the diff (judgment); it
  never decides the merge (that's code + human, per g-rl-38 "Model for Judgment Only").
- **Never blind-writes a curated cell.** `gald3r platform refresh --apply` only ever stamps
  `last_doc_scan`; `[needs-review]` capability disagreements are surfaced, never auto-resolved.
- Both `.py` canonicals are dry-run by default; `--apply` is required to write anything.

> **Status (T1460 → T647):** end-to-end wiring complete. Per-platform diff heuristics for
> `SCAN_DOCS` step 3 continue to be completed by T1461–T1483.
