# g-skl-policy

Policy-as-code guardrail skill (T1611, D12). See `SKILL.md` for the full operation reference.

Quick facts:
- `gald3r policy check` is the single shared engine verb — invoked by both
  `.claude/hooks/g-hk-policy-check.py` (pre-tool-call) and `.claude/hooks/g-hk-pre-commit.py`
  (pre-commit), so bundle-loading and rule-matching logic is authored once (g-rl-04 DRY).
- Team/Org tier only. Free/retail installs always evaluate against an empty bundle (see
  the org-tier gate; see `gald3r policy status`).
- Zero required external dependency: PyYAML is used when available, otherwise a small
  dependency-free parser handles the bundle's flat YAML shape.
- Fail-open everywhere: a missing skill, malformed bundle, or engine exception never blocks a
  tool call or commit — only an explicit `action: block` rule match does.
