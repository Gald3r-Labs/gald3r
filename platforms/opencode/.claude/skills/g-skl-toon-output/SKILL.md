---
name: g-skl-toon-output
description: Emit gald3r output as TOON (Token-Oriented Object Notation) — a compact, lossless, LLM-friendly format that states record keys once (tabular arrays) to cut tokens vs markdown/JSON. Operations ENCODE, DECODE, VALIDATE, EXPORT. Invoked by --toon flag commands (T1382). Coordination state files stay markdown.
token_budget: low
subsystem_memberships: [UI_AND_OUTPUT]
---
# g-skl-toon-output

TOON (Token-Oriented Object Notation) is a gald3r-native output format optimized for
LLM context efficiency: token-efficient, lossless, LLM-parseable, human-skimmable.
Parallel to `g-skl-html-output` (T1316) and `g-skl-json-output` (T1381).

## When to Use
- A command was invoked with `--toon` (or AGENT_CONFIG `output_format: toon`).
- Agent-to-agent handoff, context injection, or vault ingestion where markdown is too
  verbose and JSON's repeated keys waste tokens.

## Boundary (HARD)
TOON is a derived **report** view. `TASKS.md`, `BUGS.md`, `CONSTRAINTS.md`, task specs,
and any `.gald3r/` control-plane file remain markdown (source of truth).

## TOON spec (v1)

Indentation = 2 spaces. One construct per line. No closing brackets.

```
# scalars
key: value                      # bare; quote only if value has : | newline or leading/trailing space
flag: true                      # booleans/numbers/null bare
note: "has: colon, needs quote"

# nested object  (indent children)
counts:
  open: 7
  completed: 605

# scalar array (inline)
labels[3]: feature, bug, chore

# object array (TABULAR — keys stated ONCE; this is the token win)
top_tasks[2]{id,title,priority,status}:
  1381 | JSON mode | medium | in-progress
  1382 | TOON mode | medium | pending
```

Rules:
- `key[N]{f1,f2,...}:` declares an array of `N` objects with the given fields, in
  order; each following indented line is one record, fields `|`-delimited (cells are
  trimmed; a literal `|` in a cell is escaped `\|`; rows split on **unescaped** pipes
  so a trailing empty/null cell is still detected; empty cell = `null`; a quoted empty
  cell `""` is the empty string, which is how `""` is disambiguated from `null`).
- `key[N]:` followed by inline comma list is a scalar array. An empty array is `key[0]:`.
- Quoting: a string is quoted with `"` only if it (a) contains `:`, `|`, or a newline,
  (b) has leading/trailing whitespace, (c) is the empty string `""`, or (d) would
  otherwise be **coerced** on DECODE — i.e. it looks like a number (`012`), a boolean
  (`true`/`false`), or `null`. `"` inside a quoted string is escaped `\"`.
- **Safe characters (no quoting):** `%`, `#`, `!`, `@`, `*`, and a lone `\` are NOT part
  of the grammar and round-trip bare. So `completion: 87%`, `tag: #release`, and
  `path: a\b` are all valid unquoted. Only the grammar/coercion triggers above force a quote.
- The same envelope as JSON precedes `data`:
  ```
  gald3r_version: 1.2.0
  generated_at: 2026-05-20T21:30:00Z
  command: g-status
  schema: status
  data:
    ...
  ```
- **Lossless:** TOON ⇄ JSON round-trips (ENCODE then DECODE yields the original object).

## Operations

### ENCODE `<json>`
Convert a JSON object (the same envelope+data as `g-skl-json-output`) to TOON. Arrays
of uniform objects become tabular blocks; everything else maps per the grammar.

### DECODE `<toon>`
Parse TOON back to a structured object (and on to JSON if needed).

### VALIDATE
ENCODE→DECODE round-trip must equal the source object (lossless check); field counts
in `[N]{...}` must match the rows present.

Edge-case coverage beyond the inline VALIDATE smoke-test lives in
`scripts/toon_test.ps1` (T1384) — 16 round-trip assertions for deep nesting, empty /
single-element / scalar arrays, null & empty-string tabular cells, pipe-escaped cells,
numeric/bool-looking strings (preserved as strings), and safe special characters:
```powershell
uv run python .claude/skills/g-skl-toon-output/scripts/toon_test.py   # exit 0 = all pass
```

### EXPORT
Save under `html_output_dir` (default `docs/`) per `g-rl-01` with a `.toon` extension:
`YYYYMMDD_HHMMSS_<IDE>_<TOPIC>.toon`. `.toon` files are vault-ingestable via
`g-skl-vault` / `g-skl-recon-file`.

Helper: `.claude/skills/g-skl-toon-output/scripts/toon_output.ps1`
```powershell
uv run python .claude/skills/g-skl-toon-output/scripts/toon_output.py `
  -Command g-status -Schema status -DataJson $jsonString -OutDir docs -Topic STATUS
# add -Compare to print markdown-vs-TOON token estimate; -Stdout to skip the file write
```

## Token efficiency
TOON's tabular arrays state each field name once instead of per-record (JSON) or per
bullet (markdown). On a representative `g-status` payload this yields a ~20% character
(~token) reduction vs JSON and substantially more vs markdown — run with `-Compare`.
`--md`/`--toon` override AGENT_CONFIG `output_format`; default `markdown` is unchanged.
