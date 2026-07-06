---
name: g-skl-policy
tier: full
local_only: false
description: Policy-as-code guardrail — loads an org policy bundle (file offline, world_tree online) and exposes a CHECK op used by the pre-tool-call and pre-commit hooks to deterministically block/allow. Team/Org tier only; free/retail installs run an empty/default bundle.
triggers:
  - "@g-policy-check"
  - "@g-policy-status"
  - "org policy"
  - "policy bundle"
  - "policy guardrail"
operations:
  - CHECK
  - STATUS
token_budget: low
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---

# g-skl-policy

**Activate for**: `@g-policy-check`, `@g-policy-status`, org policy, policy bundle, policy guardrail (D12 — policy-as-code guardrails).

## Summary

Serves org-wide policy-as-code guardrails. A `CHECK` operation loads the active org policy
bundle and evaluates an event (a tool call, or a git commit's staged diff) against it,
returning a deterministic `allow` / `warn` / `block` verdict. **Enforcement is by code, not
model discretion** (g-rl-38): the hooks that call `CHECK` return the verdict as-is; the model's
only role is to explain the violation to the user, never to override it.

This skill is the file-side surface. `world_tree` serves the org policy bundle for online
installs; `agent` enforces the same bundle at runtime for autonomous sessions. This skill owns
the local CHECK op and the bundle-loading logic shared by both the pre-tool-call hook
(`g-hk-policy-check`) and the pre-commit hook (`g-hk-pre-commit`, section 7).

---

## Tier Gate (Team/Org only)

Org-wide policy enforcement requires **both**:
1. `.gald3r/.identity` declares a non-empty `org_id`.
2. The plan tier (`.identity`'s `plan_tier` field, or `GALD3R_PLAN_TIER` env override for
   local testing) is `team` / `org` / `organization` / `enterprise`.

Free tier and retail (no-org) installs never load or enforce another org's rules — they run an
empty/default bundle (zero rules; `CHECK` always returns `allow`) and rely on
**`g-skl-constraints`** (`.gald3r/CONSTRAINTS.md`) for local-only constraints instead. This
mirrors the T633 paywall-gate pattern: a deterministic local check with a safe default, and the
subscription/billing authority living server-side in `world_tree`.

---

## Operations

### CHECK — Evaluate an event against the active bundle

```
Usage (from a hook): gald3r policy check --json   # event JSON piped on STDIN
Usage (diagnostic):  gald3r policy status         # show the active bundle
```

Called automatically by:
- **`g-hk-policy-check`** (`.claude/hooks/`) — registered in `g_hk_core.py`'s `tool-start`
  concern chain (T424/T510), so it fans out to every hook-capable platform for free via the
  existing canonical dispatcher. Fires before each tool call; a `block` verdict returns
  `permission: deny` + exit code 2 (the tool-start blocking convention), a `warn` verdict
  surfaces `additional_context`, and `allow` is silent.
- **`g-hk-pre-commit`** (section 7, "ORG POLICY-AS-CODE GUARDRAIL") — evaluates the staged diff
  + staged file list at commit time. A `block` verdict halts the commit (same `GALD3R_HOOK_BYPASS`
  override as the rest of the pre-commit gate).

Manual invocation (diagnostics):
```bash
echo '{"command": "git push --force"}' | gald3r policy check --json
```

### STATUS — Show the active bundle

Report:
- Whether the org tier gate is enabled (`org_id` + plan tier present).
- Bundle source: `online (world_tree)` / `file (.gald3r/policy/org_policy.yaml)` / `default (empty)`.
- Rule count and each rule's `id` + `action`.

```
Org Policy Status
─────────────────
Org tier enabled: yes (org_id=acme-corp, plan_tier=team)
Bundle source:    file (.gald3r/policy/org_policy.yaml)
Rules:            2
  - no-force-push          action=block
  - warn-large-commit      action=warn
```

When the org tier gate is disabled, print:
```
Org Policy Status
─────────────────
Org tier enabled: no (free tier / no org_id — local constraints only, see g-skl-constraints)
Bundle source:    default (empty)
Rules:            0
```

---

## Bundle Format

`.gald3r/policy/org_policy.yaml` (gitignored — this is per-install local state, not
canonical template source):

```yaml
org_id: acme-corp
version: 1
rules:
  - id: no-force-push
    action: block
    message: "force-push is blocked by org policy — open a PR instead"
    match:
      command: "push --force"
  - id: warn-large-commit
    action: warn
    message: "large diffs should be split — org convention"
    match:
      staged_files: ".{50,}"
```

`match` fields are matched against the event payload (top-level, then `tool_input`/
`tool_response` nesting) via case-insensitive regex search (falls back to substring match if
the pattern isn't valid regex). ALL fields in `match` must match for the rule to fire. First
matching `block` rule wins; `warn` rules accumulate but never block.

**Bundle resolution order** (`gald3r policy check` / `gald3r policy status`):
1. Online — `GET {WORLD_TREE_URL}/api/v1/policy/{org_id}/bundle` (2s timeout, best-effort;
   any failure falls through to file). Skipped entirely when the org tier gate is disabled.
2. File — `.gald3r/policy/org_policy.yaml`.
3. Default — empty bundle (zero rules) when neither source is available.

PyYAML is used when importable; otherwise a small dependency-free parser handles the flat
shape shown above (no external install required to use this skill).

---

## Namespacing & Isolation

Each bundle is scoped to exactly one `org_id` (from `.identity`). A retail/free install has no
`org_id` and therefore never fetches or reads any org's rules — `load_bundle` short-circuits to
`EMPTY_BUNDLE` before any file or network access is attempted. There is no cross-org bundle
merging or fallback; a project belongs to at most one org.

---

## Related

- `.claude/hooks/g-hk-policy-check.py` — pre-tool-call concern hook (fans out via `g_hk_core.py`).
- `.claude/hooks/g-hk-pre-commit.py` — section 7, pre-commit enforcement.
- `.claude/skills/g-skl-constraints/` — local-only constraints (free tier / no-org path).
- `.gald3r/tasks/completed/2026/06/task633_paywall_multi_coordinator_paid_tier.md` — the T633
  tier-gate pattern this skill's tier gate mirrors (local deterministic check + safe default,
  billing authority server-side).
- `.gald3r/tasks/open/task1608_wpac_v2_repoint_verbs_world_tree_offline_fallback.md`,
  `.gald3r/tasks/open/task1609_wpac_v2_connectivity_entitlement_client_shim.md` — sibling
  world_tree connectivity work; this skill's online fetch is intentionally self-contained
  (does not depend on the not-yet-built T1609 shared client shim) so it ships independently.
