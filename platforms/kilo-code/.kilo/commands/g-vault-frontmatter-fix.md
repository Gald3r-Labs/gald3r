---
subsystem_memberships: [VAULT_AND_RESEARCH]
---
Retrofit Obsidian frontmatter onto vault notes missing it: $ARGUMENTS

Drives the T1334 retrofit helper. Adds VAULT_OBSIDIAN_STANDARD YAML frontmatter
(`date`, `type`, `ingestion_type`, `source`, `title`, `topics`) to long-lived vault
notes that lack it — `memory.md`, `sessions/*.md`, `decisions/*.md` (+ `decision_status`/
`decided_on`), `knowledge/*.md`. **Backup-first, dry-run by default, idempotent.**

## Behavior

Runs `.claude/skills/g-skl-vault/scripts/frontmatter_fix.ps1`:

1. Resolve the vault from `.gald3r/.identity` `vault_location=` (no-op when `{LOCAL}`/unset).
2. Walk `projects/*/memory.md`, `projects/*/sessions/`, `projects/*/decisions/`, `knowledge/`.
3. Skip files that already start with `---` (idempotent), and read-only / symlinked files (warned).
4. **Dry-run (default)**: print the would-be frontmatter per non-conformant file.
5. **`--apply`**: back up each file to `{vault}/.backups/{timestamp}/<relpath>` then prepend the
   block (existing content preserved byte-for-byte). UTF-8 without BOM.

```powershell
uv run python .claude/skills/g-skl-vault/scripts/frontmatter_fix.py            # dry-run
uv run python .claude/skills/g-skl-vault/scripts/frontmatter_fix.py -Apply
uv run python .claude/skills/g-skl-vault/scripts/frontmatter_fix.py -File "<path>" -Apply
```

## Flags

| Flag | Effect |
|---|---|
| `--dry-run` (default) | Report + show planned frontmatter; no writes |
| `--apply` | Write (with per-file backup); requires explicit confirmation |
| `--file <path>` | Single-file mode |

## Notes

- Type inference: `memory.md`/`sessions/` → `session`; `decisions/` → `decision`;
  `knowledge/` → `knowledge_card`. `title` comes from the leading `#` header (or filename).
- Does **not** touch `.gald3r/learned-facts.md` (project-internal, not vault-stored).
- `@g-vault-lint` flags missing frontmatter; `@g-vault-lint --auto-fix <file>` calls this on one file.
- See `VAULT_OBSIDIAN_STANDARD.md` and `g-skl-vault` § Required Frontmatter.
